from MessageFormats import Client_Update, Proposal, Server_Response
from FileOps import write_to_file_dummy, write_to_file
from pickle import loads
from ProcessVariables import LEADER_ELECTION, REG_LEADER, REG_NON_LEADER
from NetworkFunctions import send_message_using_hostname, send_message
from Proposal import send_proposals
import threading
from paxos_hash_table import HashTable


# Threading function for update timer:
def update_timer_function(my_info, client_update):
    if my_info.update_thread_flag:
        print("Update Timer expired, Sending updates back to leader and restarting timer...")
        if my_info.state == REG_NON_LEADER:
            if my_info.current_leader_hostname is not None:
                send_message_using_hostname(client_update, my_info.current_leader_hostname)
        threading.Timer(10.0, update_timer_function, args=(my_info, client_update)).start()
    else:
        print("Inside the update timer, not sending anything. Timer cancelled")


# Function to enqueue the update
def enqueue_update(client_update, server_info):
    if client_update.client_id in server_info.last_executed:
        if client_update.timestamp <= server_info.last_executed[client_update.client_id]:
            return False

    if client_update.client_id in server_info.last_enqueued:
        if client_update.timestamp <= server_info.last_enqueued[client_update.client_id]:
            return False
    server_info.update_queue.append(client_update)
    server_info.last_enqueued[client_update.client_id] = client_update.timestamp
    return True


# Function to start off an update timer for a specific client_id:
def start_update_timer(client_update, my_info):
    update_timer = threading.Timer(10.0, update_timer_function, args=(my_info, client_update))
    my_info.update_threads[client_update.client_id] = update_timer
    my_info.update_thread_flag = True
    update_timer.start()


# Function to cancel the update timer
def cancel_update_timer(running_thread):
    running_thread.cancel()
    print("Cancelled the update timer")


# Function to add the pending updates to the server
def add_to_pending_updates(client_update, server_info):
    server_info.pending_updates[client_update.client_id] = client_update
    print("Pending updates so far::")
    for cu in server_info.pending_updates.values():
        print("Client_ID:{0} Timestamp:{1} Update:{2}".format(cu.client_id, cu.timestamp, cu.update))
    # Set Update Timer(U.client id)
    # Set a unique name for the update timer (One timer for one update)
    start_update_timer(client_update, server_info)
    write_to_file(server_info)


# Function to enqueue unbound pending updates
# That is, if an update is in the pending queue, then this update needs to be bound to a sequence number
def enqueue_unbound_pending_updates(my_info):
    # Check if the update is present in the global history, bounded to a seq number,
    # If not present, check if it exists in the update_queue,
    # If not enqueue this client_update
    for cu in my_info.pending_updates.values():
        for gh in my_info.global_history.values():
            if gh['Proposal'] is not None:
                if gh['Proposal'].update.client_id == cu.client_id and gh['Proposal'].update.timestamp == cu.timestamp:
                    print("Found the same update in global history Update Client ID: {0} Update Timestamp: {1}".format(
                        cu.client_id, cu.timestamp))
                    return
        # If you reached here then this update is not bound, check if it exists in the update queue
        if cu in my_info.update_queue:
            return

        # If you reach here, then the update cu is ready to queued:
        print("Queueing a client update from pending queue to update queue")
        enqueue_update(cu, my_info)


# # Function to remove the bound updates from the queue:
def remove_bound_updates_from_queue(my_info):
    for cu in my_info.update_queue:
        # Check if this cu is bound (that is, available in global history)
        for gh in my_info.global_history.values():
            if gh['Proposal'] is not None:
                if ((gh['Proposal'].update.client_id == cu.client_id and gh[
                    'Proposal'].update.timestamp == cu.timestamp)
                        or (cu.client_id in my_info.last_executed and cu.timestamp <= my_info.last_executed[cu.client_id])
                        or (cu.timestamp <= my_info.last_enqueued[cu.client_id] and cu.server_id != my_info.pid)):
                    my_info.update_queue.remove(cu)
                    if cu.timestamp > my_info.last_enqueued[cu.client_id]:
                        my_info.last_enqueued[cu.client_id] = cu.timestamp
                        print("Updated Timestamp for client id {0}".format(cu.client_id))


# Function to handle client update according to the state the server is in
def handle_client_updates(client_update, my_info):
    if my_info.state == LEADER_ELECTION:
        if client_update.server_id == my_info.pid:
            if enqueue_update(client_update, my_info):
                add_to_pending_updates(client_update, my_info)

    if my_info.state == REG_NON_LEADER:
        if client_update.server_id == my_info.pid:
            add_to_pending_updates(client_update, my_info)
            send_message_using_hostname(client_update, my_info.current_leader_hostname)

    if my_info.state == REG_LEADER:
        print("Got a client update from a non leader")
        if enqueue_update(client_update, my_info):
            if client_update.server_id == my_info.pid:
                add_to_pending_updates(client_update, my_info)
            print("Received a Client Update when I'm the leader, need to send proposals now...")
            # Make a proposal: server_id,view,seq,update
            send_proposals(my_info)


# Dummy method for testing
def handle_client_read_request(recvd_msg, my_info, address):
    ht = HashTable('HashTable.json', True, True)
    value = ht.get(recvd_msg.key)
    client_response = Server_Response(20, my_info.pid, recvd_msg.key, value)
    send_message(client_response, address)
