import MessageFormats

REG_LEADER = 1
REG_NON_LEADER = 2
LEADER_ELECTION = 3


class ProcessVariables:

    def __init__(self, process_id):
        self.pid = process_id
        self.state = LEADER_ELECTION
        self.last_installed = -1
        self.last_attempted = -1
        self.view_change_messages = {}
        # Initial Prepare message here
        self.prepare = MessageFormats.Prepare_Message(7, process_id, -1, -1)
        # Global Ordering variables
        self.prepare_oks = {}
        self.set_timer = False
        self.local_aru = 0
        self.test_case = -1

        # dict of global slots, mapped by sequence number, each containing
        # Proposal - latest Proposal accepted for this sequence number, if any
        # Accepts[] - array of corresponding Accept messages, indexed by server id
        # Globally Ordered Update - ordered update for this sequence number, if any
        self.global_history_dict = {"Proposal": None, "Accepts": [], "Globally_Ordered_Update": None}
        # This is a dict of dicts: eg: {1:{"Proposal": None, "Accepts": [], "Globally_Ordered_Update": None}}
        self.global_history = {-1: self.global_history_dict}

        # Client Handling variables
        self.update_queue = []      # queue of Client Update messages
        self.last_executed = {}     # dict of timestamps, mapped by client id, i.e client_id : timestamp
        self.last_enqueued = {}     # dict of timestamps, mapped by client id, i.e client_id : timestamp
        self.pending_updates = {}   # dict of Client Update messages, indexed by client id, i.e client_id : update

        # Will be used when it receives an update from a client - A bit skeptical about this
        self.seq_no = 0
        self.current_leader_hostname = None
        self.all_hosts = []

        # Map for clients, the client ids are mapped to the client addresses to send data back to
        self.client_map = {}

        # Flag used for restarting progress timer after executing client update
        self.update_executed = False

        # Dictionary used for managing update timer threads
        self.update_threads = {}
        self.update_thread_flag = False



    def __str__(self):

        res = "pid : "+str(self.pid)+"\n"+"state : "+str(self.state)+"\n"+ \
                "last_attempted : "+str(self.last_attempted)+"\n"+ \
                "last_installed : "+str(self.last_installed)+"\n"+\
                "local_aru : "+str(self.local_aru)+"\n"

        return res


    
