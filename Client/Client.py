import argparse
import socket
from pickle import loads, dumps

from MessageFormats import Client_Read_Update, Client_Update
import select
import sys
from PIL import Image


PORT = 9999
BUFFER_SIZE = 1024



class ClientProcessVariables:
    def __init__(self):
        self.timestamp = 0
        self.pid = -1
        self.connected_server_id = -1
        self.connected_server = None


def __average_hash__(image_path, hash_size=8):
        """ Compute the average hash of the given image. """
        # print(image_path)
        with open(image_path, 'rb') as f:
            # Open the image, resize it and convert it to black & white.
            image = Image.open(f).resize((hash_size, hash_size), Image.ANTIALIAS).convert('L')
            pixels = list(image.getdata())

        avg = sum(pixels) / len(pixels)

        # Compute the hash based on each pixels value compared to the average.
        bits = "".join(map(lambda pixel: '1' if pixel > avg else '0', pixels))
        hashformat = "0{hashlength}x".format(hashlength=hash_size ** 2 // 4)
        return int(bits, 2).__format__(hashformat)


def get_socket(bindStatus):
    try:
        sockfd = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
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
    sockfd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    sockfd.setblocking(0)
    return sockfd


# More processing for types of user inputs here, for the time being this just handles WRITE
# On WRITE, this will form a client_update message with the value passed later on.
def process_user_input(line, my_info):

    commands = line.split(' ')
    if commands[0] == 'set':
        print("Sending data {0} to {1}".format(commands[1], my_info.connected_server_id))
        data_to_be_sent = commands[1] + " " + commands[2]
        write_data(data_to_be_sent, my_info)

    elif commands[0] == 'get':
        data_to_be_sent = commands[1]
        print("Sending a request to fetch the value of {0} to {1}".format(commands[1], my_info.connected_server_id))
        read_data(data_to_be_sent, my_info)

    elif commands[0] == 'iset':
        print("Request to store details for an image")
        commands[1] = __average_hash__(commands[1])
        data_to_be_sent = " ".join(commands[1:])
        write_data(data_to_be_sent, my_info)

    elif commands[0] == 'iget':
        print("Request to get image details")
        commands[1] = __average_hash__(commands[1])
        data_to_be_sent = " ".join(commands[1:])
        read_data(data_to_be_sent, my_info)

    else:
        print("Sorry, not supported yet")


def read_data(data_to_be_sent, my_info):
    writing_socket = get_socket(False)
    try:
        addr = socket.gethostbyname(my_info.connected_server)
        serv_addr = (addr, PORT)
    except socket.error as error:
        print("Error in getting address of server")
        exit(1)
    req_msg = Client_Read_Update(13, my_info.pid, data_to_be_sent)
    bytes_to_send = dumps(req_msg)
    num_sent = writing_socket.sendto(bytes_to_send, serv_addr)
    if num_sent < 0:
        print("No data sent")
    else:
        print("Read Request sent successfully to {0}".format(serv_addr))


def write_data(data_to_be_sent, my_info):
    writing_socket = get_socket(False)
    try:
        addr = socket.gethostbyname(my_info.connected_server)
        serv_addr = (addr, PORT)
    except socket.error as error:
        print("Error in getting address of server")
        exit(1)
    my_info.timestamp += 1
    data_message = Client_Update(12, my_info.pid, my_info.connected_server_id, my_info.timestamp, data_to_be_sent)
    bytes_to_send = dumps(data_message)
    num_sent = writing_socket.sendto(bytes_to_send, serv_addr)
    if num_sent < 0:
        print("No data sent")
    else:
        print("Data sent successfully to {0}".format(serv_addr))


if __name__ == '__main__':
    # Create a command line parser
    parser = argparse.ArgumentParser(description='Get current container name to connect to, ', add_help=False)
    # Add the arguments to be handled
    parser.add_argument('-h', type=str)
    # -p for process id of client
    parser.add_argument('-p', type=str)
    args = parser.parse_args()
    host = args.h
    pid = args.p

    connected_server_id = int(host.split('r')[1])
    my_info = ClientProcessVariables()
    my_info.connected_server_id = connected_server_id
    my_info.pid = pid
    my_info.connected_server = host
    listening_socket = get_socket(True)
    inputs = [listening_socket, sys.stdin]
    while True:
        readable, writable, _ = select.select(inputs, [], [])

        for s in readable:
            if s is listening_socket:
                # print("Got something from the server")
                msg, address = s.recvfrom(BUFFER_SIZE)
                recvd_msg = loads(msg)

                # Response to a Get Request
                if recvd_msg.type == 20:
                    # print("Got a response to a GET request")
                    print("\n------------------------------------------------------------")
                    print("Key Requested:{0} Value:{1}\n".format(recvd_msg.key, recvd_msg.value))
                    print("------------------------------------------------------------\n")

                # Response to a Write Request
                if recvd_msg.type == 21:
                    print("Got a SUCCESS message from the server for timestamp:{0} update:{1}\n"
                          .format(recvd_msg.timestamp, recvd_msg.update))

            if s is sys.stdin:
                line = sys.stdin.readline().rstrip()
                process_user_input(line, my_info)
