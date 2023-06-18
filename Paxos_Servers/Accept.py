from ClientUpdateExecution import execute_client_update
from NetworkFunctions import send_to_all_servers
from MessageFormats import Globally_Ordered_Update


# function to check for conflicts on getting an Accept
def check_conflicts_for_accept(my_info, accept_msg):
    if my_info.pid == accept_msg.server_id:
        return True
    if my_info.last_installed != accept_msg.view:
        return True
    if accept_msg.seq in my_info.global_history:
        if my_info.global_history[accept_msg.seq]['Proposal'] is not None:
            if my_info.global_history[accept_msg.seq]['Proposal'].view != accept_msg.view:
                print("Found a Proposal with the wrong view in global history of seq: {0}"
                      " Stored View: {1} New View:{2}"
                      .format(accept_msg.seq, my_info.global_history[accept_msg.seq]['Proposal'].view, accept_msg.view))
                return True
    return False


# Function to apply Accept to data structures
def apply_accept_to_ds(my_info, accept_msg):
    seq = accept_msg.seq
    # print("\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    # print("Inside apply accept to DS: Seq: {0}".format(seq))
    if accept_msg.seq in my_info.global_history:
        if my_info.global_history[seq]['Globally_Ordered_Update'] is not None:
            # gbu = my_info.global_history[seq]['Globally_Ordered_Update']
            # print("Found a GBU for the seq number with Seq Number {0} and server_id:{1}"
            #       .format(gbu.seq, gbu.server_id))
            return
        if len(my_info.global_history[seq]['Accepts']) >= int(len(my_info.all_hosts)/2):
            print("Length of accepts received so far: {0}".format(len(my_info.global_history[seq]['Accepts'])))
            return
        # Check if the accept received is already present in accepts[]
        for accept in my_info.global_history[seq]['Accepts']:
            if accept.server_id == accept_msg.server_id and accept.view == accept_msg.view:
                return
        my_info.global_history[seq]['Accepts'].append(accept_msg)
    else:
        my_info.global_history[seq] = my_info.global_history_dict
        my_info.global_history[seq]['Accepts'].append(accept_msg)
    # print("Accept Queue after applying accepts to DS for Seq {0}:".format(seq))
    # for accept in my_info.global_history[seq]['Accepts']:
    #     print("Server_id:{0} View:{1} Seq:{2}".format(accept.server_id, accept.view, accept.seq))
    # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")


# Function to check if the update is ready to be globally ordered
def globally_ordered_update(my_info, accept_msg):
    seq = accept_msg.seq
    if seq in my_info.global_history:
        if my_info.global_history[seq]['Proposal'] is not None:
            if len(my_info.global_history[seq]['Accepts']) >= int(len(my_info.all_hosts)/2):
                # Check is each accept in seq has the same view
                for accept in my_info.global_history[seq]['Accepts']:
                    if accept.view == accept_msg.view:
                        continue
                    else:
                        # print("The view matching failed for SEQ NO:{0} Stored View:{1} New View:{2}"
                        #       .format(seq, accept.view, accept_msg.view))
                        # print("******************************************************************")
                        # print("Accept messages so far for seq no:{0}:".format(seq))
                        # for ac in my_info.global_history[seq]['Accepts']:
                        #     print("Accept Message: View:{0} Seq:{1} Server_Id:{2}".format(ac.view, ac.seq, ac.server_id))
                        # print("******************************************************************\n")
                        return False
                return True
    else:
        print("SEQ NOT IN GLOBAL HISTORY")
        return False


# Function to apply the globally ordered update to data structures
def apply_globally_ordered_update_to_ds(my_info, gbu):
    if gbu.seq in my_info.global_history:
        if my_info.global_history[gbu.seq]['Globally_Ordered_Update'] is None:
            my_info.global_history[gbu.seq]['Globally_Ordered_Update'] = gbu


# Advance ARU
def advance_aru(my_info):
    i = my_info.local_aru + 1
    while True:
        if i in my_info.global_history and my_info.global_history[i]['Globally_Ordered_Update'] is not None:
            my_info.local_aru = my_info.local_aru + 1
            i = i + 1
        else:
            return


# Function to handle accept message when received:
def handle_accept(my_info, accept_msg):
    print("Handling Accept with view:{0} seq:{1}".format(accept_msg.view, accept_msg.seq))
    apply_accept_to_ds(my_info, accept_msg)
    if globally_ordered_update(my_info, accept_msg):
        # At this point, the client update should be present in the Proposal message that has been stored in
        # Global history for a particular seq number under 'Proposal'
        client_update = my_info.global_history[accept_msg.seq]['Proposal'].update
        globally_ordered_client_update = Globally_Ordered_Update(10, my_info.pid, accept_msg.seq,  client_update)
        apply_globally_ordered_update_to_ds(my_info, globally_ordered_client_update)
        advance_aru(my_info)
        print("Update globally ordered, current ARU: {0}   GBU_Seq:{1}".format(my_info.local_aru,
                                                                               globally_ordered_client_update.seq))
        if my_info.local_aru == accept_msg.seq:
            # Execute the client update
            # Need to stop this from happening twice
            if not my_info.update_executed:
                print("Executing the client update...")
                execute_client_update(my_info, accept_msg)

                return
    else:
        print("Update not globally ordered")


