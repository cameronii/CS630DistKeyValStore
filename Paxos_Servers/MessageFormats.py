class Message:

    # Type 4 = Alive Message
    # Type 5 = AliveAck Message
    def __init__(self, type):
        self.type = type


class AliveMessage(Message):
    pass


class AliveAckMessage(Message):
    pass


# Type = 2
class View_Change(Message):

    def __init__(self, type, server_id, attempted ):
        super(View_Change, self).__init__(type)
        self.server_id = server_id
        self.attempted = attempted


# Type = 3
class VC_Proof(Message):

    def __init__(self, type, server_id, installed):
        super(VC_Proof, self).__init__(type)
        self.server_id = server_id
        self.installed = installed


# Type = 6
class LeaderInstall(Message):

    def __init__(self, type, server_id, view_to_install):
        super(LeaderInstall, self).__init__(type)
        self.server_id = server_id
        self.view_to_install = view_to_install


# Type = 7
class Prepare_Message(Message):

    def __init__(self, type, server_id, view, local_aru):
        super(Prepare_Message, self).__init__(type)
        self.server_id = server_id
        self.view = view
        self.aru = local_aru


# Type = 8: Prepare_OK
class Prepare_OK(Message):
    def __init__(self, type, server_id, view, data_list):
        super(Prepare_OK, self).__init__(type)
        self.server_id = server_id
        self.view = view
        self.data_list = data_list


# Type 9 : Proposal
class Proposal(Message):
    def __init__(self, type, server_id, view, seq, update):
        super(Proposal,self).__init__(type)
        self.server_id = server_id        #unique identifier of the sending server
        self.view = view                  #the view in which this proposal is being made
        self.seq = seq                    #the sequence number of this proposal
        self.update = update              #the client update being bound to seq in this proposal


# Type 10 : Globally Ordered Update
class Globally_Ordered_Update(Message):
    def __init__(self,type,server_id,seq,update):
        super(Globally_Ordered_Update,self).__init__(type)
        self.server_id = server_id     #unique identifier of the sending server
        self.seq = seq                 #the sequence number of the update that was ordered
        self.update = update           #the client update bound to seq and globally ordered


# Type 11 : Accept Message
class Accept(Message):
    def __init__(self,type,server_id,view,seq):
        super(Accept,self).__init__(type)
        self.server_id = server_id  #unique identifier of the sending server
        self.view = view            #the view for which this message applies
        self.seq = seq              #the sequence number of the associated Proposal


# Type 12: Client Update
# For now, let's just assume that "update" field will have the value to be written to a file
# We can classify update later
class Client_Update(Message):
    def __init__(self, type, client_id, server_id, timestamp, update):
        super(Client_Update, self).__init__(type)
        self.client_id = client_id
        self.server_id = server_id
        self.timestamp = timestamp
        self.update = update


# Type 13 : Client Key Update
# Send a key to the server to fetch the value of the key
class Client_Read_Update(Message):
    def __init__(self, type, client_id, key):
        super(Client_Read_Update, self).__init__(type)
        self.client_id = client_id
        self.key = key


# Type 14: Reconciliation request
class Reconciliation_Request(Message):

    def __init__(self, type, server_id, aru):
        super(Reconciliation_Request, self).__init__(type)
        self.server_id = server_id                      # Server id of sending server
        self.aru = aru                      # Local Aru of sending server


# Type 15: Reconciliation
class Reconciliation(Message):

    def __init__(self, type, server_id, aru, gh_dict):
        super(Reconciliation, self).__init__(type)
        self.server_id = server_id
        self.aru = aru
        # This is the dict of all the global history entries(Globally Ordered Updates
        # and Proposals) that a server might have missed
        self.gh_dict = gh_dict


# Type 16: Reconciliation request
class Periodic_Reconciliation(Message):

    def __init__(self, type, server_id, aru):
        super(Periodic_Reconciliation, self).__init__(type)
        self.server_id = server_id  # Server id
        self.aru = aru  # Local aru of sending server


# Type 20 : Reply from server
class Server_Response(Message):
    def __init__(self, type, server_id, key, value):
        super(Server_Response, self).__init__(type)
        self.server_id = server_id
        self.key = key
        self.value = value


# Type 21: Success Message for a Write Update
class Write_Success(Message):
    def __init__(self, type, server_id, timestamp, update):
        super(Write_Success, self).__init__(type)
        self.server_id = server_id
        self.timestamp = timestamp
        self.update = update
