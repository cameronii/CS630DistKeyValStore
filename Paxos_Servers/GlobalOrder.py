from MessageFormats import Proposal,Accept,Globally_Ordered_Update
from NetworkFunctions import send_to_all_servers
from FileOps import write_to_file
import collections



def applyProposalToDS(proposal_message,server_info):
	global_history = server_info.global_history
	seq_number  = proposal_message.seq


	#on receiving first or proposal for a new seq number
	if(seq_number not in global_history):
		 gh_dict = {}
		 gh_dict["Proposal"] = proposal_message
		 gh_dict["Accepts"] = []
		 gh_dict["Globally_Ordered_Update"] = None

		 server_info.global_history[seq_number]=gh_dict


	#on receiving proposal for a already existing seq number
	else:
		gh_dict = global_history[seq_number]

		if(not gh_dict["Globally_Ordered_Update"]):
			if(gh_dict["Proposal"]  and proposal_message.view > gh_dict["Proposal"].view ):
				gh_dict["Proposal"] = proposal_message
				gh_dict["Accepts"] = []

			elif(not gh_dict["Proposal"]):
				gh_dict["Proposal"] = proposal_message


def applyAcceptToDS(acceptMessage,server_info,all_hosts):

	global_history = server_info.global_history
	seq_number  = acceptMessage.seq


	#Assuming when seq number aready exists
	if(seq_number in global_history):
		gh_dict = global_history[seq_number]

		if(gh_dict["Globally_Ordered_Update"]):
			print("global history already has GlobOrdUpdt for this seq nmber ",seq_number)
			return 


		count = 0
		accept_array = gh_dict["Accepts"]


		for i in range(len(accept_array)):
			if(accept_array[i]):
				count+=1

				if(count >= (len(all_hosts)//2)):
					print("Accept array already has majority of accept message for this seq ",seq_number)
					return 

		if(acceptMessage.server_id < len(accept_array) and accept_array[acceptMessage.server_id]):
			print("Accept array already has message for sender : {0}".format(acceptMessage.server_id))
			return 

		accept_array.append(acceptMessage)

	else:
		print("received accpt message for seq nmber not existing in global history ",seq_number)
		return



def applyGloballyOrderedUpdateToDS(gouMessage,serve_info):
	global_history = serve_info.global_history
	seq_number = gouMessage.seq

	#assuming seq is already present
	if(seq_number in global_history and not global_history["Globally_Ordered_Update"]):
		global_history["Globally_Ordered_Update"] = gouMessage



def Globally_Ordered_Ready(seq,serve_info,all_hosts):
	global_history  = serve_info.global_history

	#assuming seq already in GH
	gh_dict = global_history[seq_number]
	if(gh_dict["Proposal"]):
		d = collections.defaultdict("int")

		accept_array = gh_dict["Accepts"]
		for i in range(len(accept_array)):
			d[accept_array[i].view]+=1
			if(d[accept_array[i].view] >= (len(all_hosts)//2)):
				return True

	return False






def handleProposal(proposal_message,server_info,all_hosts):

	#apply proposal message to Data Structure
	applyProposalToDS(proposal_message,server_info)

	#construct Accept message
	acceptMessage = Accept(11,server_info.pid,proposal_message.view,proposal_message.seq)

	## synch to disc ##
	## write central data or proposal message?
	## writeToFile()

	#Send accept message to all Servers
	send_to_all_servers(acceptMessage,all_hosts)


def handleAccept(acceptMessage,server_info,all_hosts):

	#apply ccept to data structure
	applyAcceptToDS(acceptMessage,server_info)


	if(Globally_Ordered_Ready(acceptMessage.seq,serve_info,all_hosts)):
		#The last paramter here is supposed to be client update
		globally_ordered_update_message = Globally_Ordered_Ready(10,serve_info.pid,acceptMessage.seq,None)

		#apply GlobOrdMsg to DS
		applyGloballyOrderedUpdateToDS(globally_ordered_update_message,serve_info)

		#advance Aru
		#Based on executing clinet updates?












						




