# Import statements
import argparse
import select
from pickle import loads, dumps
import queue
from NetworkFunctions import are_all_nodes_up, send_to_all_servers, get_socket
from MessageFormats import AliveAckMessage, AliveMessage, Message, VC_Proof, View_Change
import time
import threading
from Prepare import check_conflict_for_prepare_message, handle_prepare_message, shift_to_prepare_phase, handle_prepare_ok
from Proposal import check_conflict_for_proposal, handle_proposal
from Reconciliation import send_periodic_reconciliation_message, handle_periodic_reconciliation_message, \
    handle_reconciliation_request, handle_reconciliation_message
from ViewChange import shift_to_leader_election, handle_view_change_message, leader_of_last_attempted, \
    handle_vc_proof_messages, pre_install_ready
from ClientFuntions import handle_client_read_request, handle_client_updates
from Accept import handle_accept, check_conflicts_for_accept
from Recovery import recover

# Constants defined here
PORT = 9999
LOCAL_ADDRESS = "127.0.0.1"
BUFFER_SIZE = 1024


def timer_thread(sleep_time):
    # print("Starting:: {0} Progress_Timer: {1}".format(threading.current_thread().getName(), sleep_time))
    time.sleep(sleep_time)
    # print("Exiting:: {0}".format(threading.current_thread().getName()))


# Thread function to send VC_Proof messages every 5 seconds (Hopefully)
def thread_send_vc_proof(my_info, last_installed_queue, last_installed_view):
    # Send VC Proof messages to everyone
    # if my_info.last_installed == my_info.last_attempted:
    if not last_installed_queue.empty():
        last_installed = last_installed_queue.get()
    else:
        last_installed = last_installed_view
    # print("IN VC_PROOF SEND: Sending a vc_proof message with last_installed as:{0}".format(last_installed))
    vc_proof = VC_Proof(3, my_info.pid, last_installed)
    send_to_all_servers(vc_proof, all_hosts)
    threading.Timer(10.0, thread_send_vc_proof, args=(my_info, last_installed_queue, my_info.last_installed)).start()


# Thread function to keep sending reconciliation messages periodically
def thread_send_reconciliation_message(my_info):
    send_periodic_reconciliation_message(my_info)
    threading.Timer(7.0, thread_send_reconciliation_message, args=(my_info, )).start()


# Read all hostnames from a file
def get_all_hosts(file_name):
    with open(file_name, 'r') as reader:
        list_of_hosts = reader.read().splitlines()
    return list_of_hosts


# Remove a container provided in the argument
def remove_node_from_list(list_of_nodes, node_to_remove):
    list_of_nodes.remove(node_to_remove)
    return list_of_nodes


# Main function
if __name__ == '__main__':
    # Create a command line parser
    parser = argparse.ArgumentParser(description='Get current container name, hostfile and other stuff', add_help=False)
    # Add the arguments to be handled
    parser.add_argument('-h', type=str)
    parser.add_argument('-n', type=str)
    parser.add_argument('-t', type=int)
    args = parser.parse_args()

    # Set variables with the arguments
    host_file = args.h
    my_name = args.n
    test_case = args.t

    # Initialize all data structures for this process:
    process_id = int(my_name.split('r')[1])
    my_info = recover(process_id)
    print("My process_id is::{0}".format(my_info.pid))
    hosts = get_all_hosts(host_file)
    my_info.test_case = test_case

    # Call a function to check if all the nodes are alive.
    print("Checking to see if all nodes are up...")
    # Remove my name from the list before checking
    hosts = remove_node_from_list(hosts, my_name)
    if are_all_nodes_up(hosts, my_info):
        print("All nodes are up")
    else:
        exit(1)

    # All nodes are up, get all the hosts and start the algorithm
    all_hosts = get_all_hosts(host_file)
    my_info.all_hosts = all_hosts
    total_hosts = len(all_hosts)
    listening_socket = get_socket(True)
    inputs = [listening_socket]
    progress_timer = 10
    t = threading.Thread(target=timer_thread, args=(progress_timer,), name='T')
    t_new = threading.Thread()
    my_info.set_timer = True
    t.start()
    installed_queue = queue.Queue()

    vc_proof_thread = threading.Timer(5.0, thread_send_vc_proof, args=(my_info, installed_queue, my_info.last_installed))
    vc_proof_thread.start()
    vc_proof_flag = True

    reconciliation_thread = threading.Timer(7.0, thread_send_reconciliation_message, args=(my_info, ))
    reconciliation_thread.start()

    while True:
        timeout = 5
        if (not t.is_alive()) and my_info.set_timer:
            if not my_info.update_executed:
                my_info.set_timer = False
                my_info.update_executed = False
                print("\n Starting a new View Change...\n")
                shift_to_leader_election(my_info.last_attempted+1, all_hosts, my_info)
            else:
                print("Restarting progress timer; Leader is still alive")
                my_info.update_executed = False
                t = threading.Thread(target=timer_thread, args=(progress_timer,), name='T2')
                t.start()

        # Select and start receiving different messages
        try:
            input_ready, _, _ = select.select(inputs, [], [], 5)
        except select.error as error:
            print("Error in select while running paxos :{0}".format(error))
        for s in input_ready:
            if s is listening_socket:
                msg, address = s.recvfrom(BUFFER_SIZE)
                recvd_msg = loads(msg)
                # If received message is a View_Change message
                if recvd_msg.type == 2:
                    # print("Received a view change message from {0}".format(recvd_msg.server_id))
                    handle_view_change_message(recvd_msg, my_info)
                    if pre_install_ready(recvd_msg.attempted, my_info, total_hosts):
                        # print(" \nPRE-INSTALL PHASE \n")
                        if not my_info.set_timer:
                            t = threading.Thread(target=timer_thread, args=(progress_timer,), name='T2')
                            t.start()
                            my_info.set_timer = True
                            # print("Checking to see if I am the leader for this view")
                            # print("Installing view {0}, since we have a majority of VC messages."
                            # .format(my_info.last_attempted))
                            my_info.last_installed = my_info.last_attempted
                            installed_queue.put(my_info.last_installed, block=False)
                            if leader_of_last_attempted(my_info.pid, my_info.last_attempted, total_hosts, my_info):
                                shift_to_prepare_phase(my_info, all_hosts)

                # If received message is a VC Proof message:
                if recvd_msg.type == 3:
                    # print("Received a VC Proof for Installed View: {0} message from {1}".format(recvd_msg.installed,
                    #                                                                             recvd_msg.server_id))
                    vc_proof_msg = VC_Proof(recvd_msg.type, recvd_msg.server_id, recvd_msg.installed)
                    handle_vc_proof_messages(vc_proof_msg, my_info, all_hosts)
                    # print("\n -------------------------------------------------")
                    # print("After handling VC Proof Message: Timer Flag: {0} Attempted: {1}  Installed: {2}\n"
                    #       .format(my_info.set_timer, my_info.last_attempted, my_info.last_installed))

                # If received message is a Prepare Message:
                if recvd_msg.type == 7:
                    # print("Received a Prepare Message")
                    if not check_conflict_for_prepare_message(recvd_msg, my_info):
                        handle_prepare_message(recvd_msg, my_info, address, total_hosts)

                # If received message is a Prepare OK:
                if recvd_msg.type == 8:
                    # print("Received Prepare OK")
                    handle_prepare_ok(recvd_msg, my_info, all_hosts)

                # if received message is a Proposal
                if recvd_msg.type == 9:
                    print("Received Proposal with the following details: ")
                    print("Server_ID: {0}   View: {1}   Seq: {2}  Update:{3}".format(recvd_msg.server_id, recvd_msg.view
                                                                                     , recvd_msg.seq, recvd_msg.update.update))
                    if not check_conflict_for_proposal(my_info, recvd_msg):
                        # print("No conflicts in proposal received")
                        handle_proposal(my_info, recvd_msg)
                    # handleProposal(recvd_msg,my_info,all_hosts)
                #
                # if received message is a Accept
                if recvd_msg.type == 11:
                    if not check_conflicts_for_accept(my_info, recvd_msg):
                        # print("Received Accept")
                        handle_accept(my_info, recvd_msg)

                if recvd_msg.type == 12:
                    print("Client Write update received ")
                    my_info.client_map[recvd_msg.client_id] = address
                    handle_client_updates(recvd_msg, my_info)

                if recvd_msg.type == 13:
                    print("Client Read Request received")
                    handle_client_read_request(recvd_msg, my_info, address)

                if recvd_msg.type == 14:
                    print("Received a reconciliation request with aru:{0} and my local_aru:{1}"
                          .format(recvd_msg.aru, my_info.local_aru))
                    handle_reconciliation_request(recvd_msg, my_info, address)

                if recvd_msg.type == 15:
                    print("Received a response to my reconciliation request. My aru:{0} Recvd_ARU:{1} from "
                          "server_id:{2} ".format(my_info.local_aru, recvd_msg.aru,  recvd_msg.server_id))
                    handle_reconciliation_message(recvd_msg, my_info)

                if recvd_msg.type == 16:
                    # print("Received periodic reconciliation message with aru:{0} from server_id:{1}"
                    #       .format(recvd_msg.aru, recvd_msg.server_id))
                    handle_periodic_reconciliation_message(recvd_msg, my_info, address)
