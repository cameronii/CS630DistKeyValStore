import socket
from MessageFormats import AliveAckMessage, AliveMessage, Message, VC_Proof
from pickle import loads, dumps
import select

PORT = 9999
BUFFER_SIZE = 1024


# Check if all the nodes in the network are up and running
def are_all_nodes_up(hosts, my_info):
    listening_socket = get_socket(True)
    writing_socket = get_socket(False)
    while True:
        inputs = [listening_socket]
        timeout = 10
        try:
            input_ready, _, _ = select.select(inputs, [], [], timeout)
        except select.error as e:
            print("Error in select::{0}".format(e))
            exit(1)
        for s in input_ready:
            if s is listening_socket:
                # print("Ready to listen!")
                msg, address = s.recvfrom(BUFFER_SIZE)
                recvd_msg = loads(msg)
                # print("Received a message of type {0} from {1}".format(recvd_msg.type, address))
                if recvd_msg.type == 4:
                    # print("Received an Alive Message, sending an AliveAck Message")
                    # Received an alive message, send an alive ack message and remove that host from the list
                    alive_ack_msg = Message(5)
                    alive_ack_to_send = dumps(alive_ack_msg)
                    num_sent = s.sendto(alive_ack_to_send, (address[0], PORT))
                    if num_sent < 0:
                        print("Could not send an Alive Ack Message")
                        continue
                    # else:
                        # print("Sent Alive Ack to: {0}".format(address))
                    # print("Removing the host from the list after sending ACK. Address:{0}, Resolved:{1}"
                    #  .format(address[0], socket.gethostbyaddr(address[0])[0].split('.')[0]))
                    if socket.gethostbyaddr(address[0])[0].split('.')[0] in hosts:
                        hosts.remove(socket.gethostbyaddr(address[0])[0].split('.')[0])
                if recvd_msg.type == 5:
                    # print("Received an AliveAck Message, removing that server")
                    # print("Received ACK, removing: Address:{0}, Resolved:{1}".format(
                    #     address[0], socket.gethostbyaddr(address[0])[0].split('.')[0]))
                    if socket.gethostbyaddr(address[0])[0].split('.')[0] in hosts:
                        hosts.remove(socket.gethostbyaddr(address[0])[0].split('.')[0])

                if recvd_msg.type == 3:
                    # Received a VC_Proof message
                    vc_proof_msg = VC_Proof(3, recvd_msg.server_id, recvd_msg.type)
                    my_info.last_attempted = vc_proof_msg.installed
                    my_info.last_installed = vc_proof_msg.installed
                    return True

        for host in hosts:
            try:
                addr = socket.gethostbyname(host)
            except socket.error as error:
                continue
            serv_addr = (addr, PORT)
            # print("Sending Alive Message to {0} : {1} ".format(host, serv_addr))
            alive_msg = AliveMessage(4)
            bytes_to_send = dumps(alive_msg)
            num_sent = writing_socket.sendto(bytes_to_send, serv_addr)
            if num_sent < 0:
                print("No data sent")
            # else:
            #     print("Data sent")
        if not hosts:
            listening_socket.close()
            writing_socket.close()
            return True
    return False


def get_socket(bindStatus):
    try:
        sockfd = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        sockfd.setblocking(0)
        # print("SOCKET")
        # print(sockfd)
    except socket.error as msg:
        print("Error while calling socket:: " + msg)
        socket.close(sockfd)
    if bindStatus:
        try:
            sockfd.bind(('', PORT))
            # print("Binded listening socket!")
        except socket.error as msg:
            print("Error in binding:: " + msg)
            socket.close(sockfd)

    return sockfd


def send_to_all_servers(msg_to_send, hosts):
    temp_hosts = hosts
    writing_socket = get_socket(False)
    bytes_to_send = dumps(msg_to_send)
    for host in temp_hosts:
        try:
            addr = socket.gethostbyname(host)
        except socket.error as error:
            # print("Error in gethostbyname:{0} \n Sending to other nodes...".format(error))
            continue
        serv_addr = (addr, PORT)
        # print("Sending message of type: {0} to {1}:{2}".format(msg_to_send.type, host, serv_addr))
        num_sent = writing_socket.sendto(bytes_to_send, serv_addr)
        if num_sent < 0:
            print("No data sent for msg type:{0}".format(msg_to_send.type))
    writing_socket.close()


def send_message(msg_to_send, address):
    bytes_to_send = dumps(msg_to_send)
    writing_socket = get_socket(False)
    leader_address = (address[0], PORT)
    try:
        # print("Sending a message of type {0} to {1}".format(msg_to_send.type, leader_address))
        num_sent = writing_socket.sendto(bytes_to_send, leader_address)
    except socket.error as error:
        print("Error sending message of type {0} to {1}::".format(msg_to_send.type, leader_address))
    writing_socket.close()


def send_message_using_hostname(msg_to_send, hostname):
    bytes_to_send = dumps(msg_to_send)
    writing_socket = get_socket(False)
    try:
        addr = socket.gethostbyname(hostname)
    except socket.error as error:
        print("Error in gethostbyname in send_message_using_hostname:{0} \n ".format(error))
    serv_addr = (addr, PORT)
    num_sent = writing_socket.sendto(bytes_to_send, serv_addr)
    if num_sent < 0:
        print("No data sent for msg type:{0}".format(msg_to_send.type))
    writing_socket.close()
