from Accept import apply_globally_ordered_update_to_ds
from ClientFuntions import enqueue_unbound_pending_updates, remove_bound_updates_from_queue
from Proposal import send_proposals, apply_proposal_to_ds

from ProcessVariables import LEADER_ELECTION, REG_LEADER, REG_NON_LEADER
from MessageFormats import Prepare_Message, Prepare_OK
from NetworkFunctions import send_message, send_to_all_servers
from FileOps import write_to_file

# Flag only used for checking if the leader has installed the view, this is to prevent the leader to go into
# shift_to_reg_leader() every time a prepare ok comes after majority is reached.
leader_view_installed = False


# Print the current leader of this view, this also sets the current leader in my_info
def print_leader(my_info, total_hosts):
    current_view_leader = my_info.last_attempted % total_hosts
    print("\n<{0}> :: Server {1} is the new leader of view {2}.\n".format(my_info.pid, current_view_leader,
                                                                          my_info.last_attempted))
    my_info.current_leader_hostname = get_hostname_of_current_leader(current_view_leader, my_info)
    print_global_history(my_info)


# Function for checking the global history in each view:
def print_global_history(my_info):
    if len(my_info.global_history) > 0:
        print("\n**************************************************************")
        print("Global History so far:")
        for gh in my_info.global_history:
            print("\nGH Index Number:{0}".format(gh))
            if my_info.global_history[gh]['Proposal'] is not None:
                print("Proposal Details:")
                prop = my_info.global_history[gh]['Proposal']
                print("server_id:{0} view:{1} seq:{2}  update:{3}".format(prop.server_id, prop.view, prop.seq,
                                                                          prop.update.update))
            print("Accepts:")
            for a in my_info.global_history[gh]['Accepts']:
                print("server_id:{0} view:{1} seq:{2}".format(a.server_id, a.view, a.seq))

            if my_info.global_history[gh]['Globally_Ordered_Update'] is not None:
                print("Globally_Ordered_Update:")
                gbu = my_info.global_history[gh]['Globally_Ordered_Update']
                print("server_id:{0} seq:{1} update:{2}".format(gbu.server_id, gbu.seq, gbu.update.update))
        print("\n Local ARU: {0}".format(my_info.local_aru))
        print("**************************************************************\n")


# Check for conflicts in the received prepare message
def check_conflict_for_prepare_message(prepare_msg, my_info):
    if prepare_msg.server_id == my_info.pid:
        return True
    if prepare_msg.view != my_info.last_attempted:
        return True
    return False


# Update data structures for a prepare message:
def update_prepare_to_data_structures(prepare_msg, my_info):
    my_info.prepare = prepare_msg


# Update data structures on receiving a prepare ok:
def update_prepare_ok_to_data_structures(prepare_ok_msg, my_info):
    if prepare_ok_msg.server_id not in my_info.prepare_oks:
        my_info.prepare_oks[prepare_ok_msg.server_id] = prepare_ok_msg
    if prepare_ok_msg.data_list:
        for d in prepare_ok_msg.data_list:
            # If this is Proposal:
            if d is not None and d.type == 9:
                apply_proposal_to_ds(my_info, d)

            # If this is a Globally Ordered Update:
            if d is not None and d.type == 10:
                apply_globally_ordered_update_to_ds(my_info, d)


# Handle prepare_ok messages here:
def handle_prepare_ok(prepare_ok_msg, my_info, all_hosts):
    update_prepare_ok_to_data_structures(prepare_ok_msg, my_info)
    global leader_view_installed
    if not leader_view_installed:
        if view_prepared_ready(prepare_ok_msg.view, my_info, len(all_hosts)):
            print("\nPrepare phase over, let's shift to leader....\n")
            print_leader(my_info, len(all_hosts))
            shift_to_reg_leader(my_info)


# Check if you have received enough prepare_oks
def view_prepared_ready(view, my_info, total_hosts_number):
    if len(my_info.prepare_oks) >= (int(total_hosts_number / 2) + 1):
        for po in my_info.prepare_oks.values():
            if po.view == view:
                continue
            else:
                return False
        global leader_view_installed
        leader_view_installed = True
        return True


def handle_prepare_message(prepare_msg, my_info, address, total_hosts):
    # print("Handling prepare message")
    if my_info.state == LEADER_ELECTION:
        update_prepare_to_data_structures(prepare_msg, my_info)
        data_list = construct_data_list(my_info, prepare_msg.aru)
        prepare_ok = Prepare_OK(8, my_info.pid, prepare_msg.view, data_list)
        my_info.prepare_oks[my_info.pid] = prepare_ok
        shift_to_reg_non_leader(my_info)
        print("Sending Prepare OK to leader...")
        send_message(prepare_ok, address)
        print_leader(my_info, total_hosts)
    else:
        # Already installed the view
        if my_info.pid in my_info.prepare_oks:
            prepare_ok = my_info.prepare_oks.get(my_info.pid)
            send_message(prepare_ok, address)
        print_leader(my_info, total_hosts)


# Shift to prepare phase for leader:
def shift_to_prepare_phase(my_info, all_hosts):
    # print("In prepare phase, getting ready to send prepare to all servers...")
    my_info.last_installed = my_info.last_attempted
    prepare_msg = Prepare_Message(7, my_info.pid, my_info.last_installed, my_info.local_aru)
    update_prepare_to_data_structures(prepare_msg, my_info)
    data_list = construct_data_list(my_info, my_info.local_aru)
    prepare_ok = Prepare_OK(8, my_info.pid, my_info.last_installed, data_list)
    my_info.prepare_oks[my_info.pid] = prepare_ok
    my_info.last_enqueued.clear()
    write_to_file(my_info)
    send_to_all_servers(prepare_msg, all_hosts)


# Construct data_list to send to all leader
def construct_data_list(my_info, aru):
    # print("Making a data list")
    data_list = []
    for i in my_info.global_history:
        if i > aru and my_info.global_history[i]:
            if my_info.global_history[i]['Globally_Ordered_Update'] is not None:
                data_list.append(my_info.global_history[i].get('Globally_Ordered_Update'))
            else:
                data_list.append(my_info.global_history[i].get("Proposal"))
    return data_list


# Get the hostname of the current leader given the id of the server
def get_hostname_of_current_leader(server_id, my_info):
    for host in my_info.all_hosts:
        if host.split('r')[1] == str(server_id):
            return host
    return None


# Function to shift to regular non leader
def shift_to_reg_non_leader(my_info):
    my_info.state = REG_NON_LEADER
    my_info.last_installed = my_info.last_attempted
    my_info.update_queue.clear()
    write_to_file(my_info)


# Function to shift to regular leader
def shift_to_reg_leader(my_info):
    my_info.state = REG_LEADER
    enqueue_unbound_pending_updates(my_info)
    remove_bound_updates_from_queue(my_info)
    my_info.last_proposed = my_info.local_aru
    send_proposals(my_info)
