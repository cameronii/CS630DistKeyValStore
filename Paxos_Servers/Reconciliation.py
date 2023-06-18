from ClientUpdateExecution import execute_client_update
from NetworkFunctions import send_message_using_hostname, send_message, send_to_all_servers
from MessageFormats import Periodic_Reconciliation, Reconciliation, Reconciliation_Request, Accept


# Function to send a reconciliation message to a random server
def send_periodic_reconciliation_message(my_info):
    reconciliation_message = Periodic_Reconciliation(16, my_info.pid, my_info.local_aru)
    send_to_all_servers(reconciliation_message, my_info.all_hosts)


# Function to handle a periodic reconciliation message received
def handle_periodic_reconciliation_message(r_msg, my_info, address):
    if r_msg.aru > my_info.local_aru:
        # Form a request to get all missed updates
        reconciliation_request = Reconciliation_Request(14, my_info.pid, my_info.local_aru)
        # Need to send to only one random server
        send_message(reconciliation_request, address)


# Function to handle a reconciliation request
def handle_reconciliation_request(r_msg, my_info, address):
    sender_aru = r_msg.aru
    gh_dict = {}
    for gh in range(sender_aru, my_info.local_aru+1):
        if gh in my_info.global_history:
            gh_dict[gh] = {"Proposal": None, "Accepts": [], "Globally_Ordered_Update": None}
            if my_info.global_history[gh]['Proposal'] and my_info.global_history[gh]['Proposal'] is not None:
                gh_dict[gh]['Proposal'] = my_info.global_history[gh]['Proposal']
            if my_info.global_history[gh]['Globally_Ordered_Update'] and \
                    my_info.global_history[gh]['Globally_Ordered_Update'] is not None:
                gh_dict[gh]['Globally_Ordered_Update'] = my_info.global_history[gh]['Globally_Ordered_Update']
    reconciliation_message = Reconciliation(15, my_info.pid, my_info.local_aru, gh_dict)
    send_message(reconciliation_message, address)


# Function to handle the reconciliation message that has all the missed updates:
def handle_reconciliation_message(r_msg, my_info):
    if len(r_msg.gh_dict) > 0 and r_msg.aru > my_info.local_aru:
        gh_dict = r_msg.gh_dict
        for gh in gh_dict:
            my_info.global_history[gh] = {"Proposal": None, "Accepts": [], "Globally_Ordered_Update": None}
            if gh_dict[gh]['Proposal'] is not None:
                my_info.global_history[gh]['Proposal'] = gh_dict[gh]['Proposal']
            if gh_dict[gh]['Globally_Ordered_Update'] is not None:
                my_info.global_history[gh]['Globally_Ordered_Update'] = gh_dict[gh]['Globally_Ordered_Update']
            # Form a dummy accept message to execute the client updates
            accept_msg = Accept(11, my_info.pid, my_info.last_installed, gh)
            print("Executing an update in reconciliation")
            execute_client_update(my_info, accept_msg)


