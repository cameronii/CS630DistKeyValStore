from MessageFormats import AliveAckMessage, AliveMessage, Message, VC_Proof, View_Change
from Prepare import shift_to_prepare_phase, shift_to_reg_non_leader
from ProcessVariables import ProcessVariables, LEADER_ELECTION, REG_NON_LEADER, REG_LEADER
from NetworkFunctions import are_all_nodes_up, send_to_all_servers, get_socket


# Function to clear the data structures for my process during view change
def clear_data_structures_for_vc(my_info):
    my_info.view_change_messages.clear()
    my_info.prepare_oks.clear()
    my_info.last_enqueued.clear()
    my_info.prepare = None


# Function to apply the given view change message to the process's data structures
def apply_vc_to_data_structures(view_change_msg, my_info):
    # Remove any old vc messages if any
    for vc_msg in my_info.view_change_messages.values():
        if vc_msg.attempted < view_change_msg.attempted:
            if view_change_msg.server_id in my_info.view_change_messages:
                del my_info.view_change_messages[view_change_msg.server_id]
                print("Deleted old stuff")
    if view_change_msg.server_id in my_info.view_change_messages:
        return
    my_info.view_change_messages[view_change_msg.server_id] = view_change_msg


# Function for initiating the leader election protocol
def shift_to_leader_election(view, all_hosts, my_info):
    # print("Shifted to leader election")
    my_info.state = LEADER_ELECTION
    clear_data_structures_for_vc(my_info)
    my_info.last_attempted = view
    vc = View_Change(2, my_info.pid, my_info.last_attempted)
    # print("Sending vc messages to everyone...")
    send_to_all_servers(vc, all_hosts)
    apply_vc_to_data_structures(vc, my_info)


# Function to handle any incoming View_Change messages
def handle_view_change_message(recvd_msg, my_info):
    # print("Received a View Change Message from {0}".format(address))
    # print("My Last Attempted : {0}, Received last attempted : {1} Sending_Server: {2}". format(my_info.last_attempted,
    #                                                                        recvd_msg.attempted, recvd_msg.server_id))
    vc_msg = View_Change(recvd_msg.type, recvd_msg.server_id, recvd_msg.attempted)
    if vc_msg.attempted == my_info.last_attempted:
        apply_vc_to_data_structures(vc_msg, my_info)


# Function to check if the process is ready for pre-installation of a view
def pre_install_ready(view, my_info, total_hosts):
    if len(my_info.view_change_messages) >= (int(total_hosts/2)+1):
        for vc in my_info.view_change_messages.values():
            if vc.attempted == view:
                continue
            else:
                return False
        return True


def leader_of_last_attempted(process_id, last_attempted, N, my_info):
    current_view_leader = last_attempted % N
    if process_id == current_view_leader:
        my_info.state = REG_LEADER
    return process_id == current_view_leader


# Function to handle VC_Proof Messages
def handle_vc_proof_messages(vc_proof_msg, my_info, all_hosts):
    if vc_proof_msg.installed > my_info.last_installed:
        my_info.last_attempted = vc_proof_msg.installed
        # my_info.last_installed = vc_proof_msg.installed
        print("UPDATED VIEW TO: {0} ".format(my_info.last_attempted))
        if not my_info.set_timer:
            my_info.set_timer = True
        if leader_of_last_attempted(my_info.pid, my_info.last_attempted, len(all_hosts), my_info):
            shift_to_prepare_phase(my_info, all_hosts)
        else:
            shift_to_reg_non_leader(my_info)

#
# def leader_sent_vc_message(my_info):
#     current_view_leader = my_info.last_attempted % total_hosts
#     if current_view_leader in my_info.view_change_messages:
#         return True
#     return False
