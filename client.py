import socket
import select
import sys
import time
import threading
import random

from class_objects import Request, Stream
import flooding_algorithm as flood
from utils import host_ip, BUFF_SIZE


TIMEOUT = 3
List_of_streams = []
Active_neighbours = []
Request_dict = dict()  # ((Request_ID, origin_IP) : Request_OBJECT)

service_controller_ip = '10.0.1.10'
port = 9090

OFF_flag = threading.Event()


def send_join_request(socket):
    """
    This function sends a join request message to a specified IP address and port using a socket.
    
    :param socket: The `socket` parameter is a Python socket object that is used to send the join
    request message to a remote server. The socket object is created using the `socket` module in Python
    and is used to establish a network connection between the client and the server
    """
    message = 'C|0|'
    socket.sendto(message.encode(), (service_controller_ip, port))


def control_message_handle(response, socket):
    """
    The function handles a control message by updating global variables and requesting a stream.
    
    :param response: It is a list containing information received from a control message
    :param socket: The `socket` parameter is likely a reference to a network socket object, which is
    used to communicate with other nodes in a network. It is probably being passed to the
    `control_message_handle` function so that it can send requests for data streams to other nodes
    """
    global Active_neighbours
    global List_of_streams

    Active_neighbours = list(response[2].split(';'))
    List_of_streams = [
        Stream(*s_info.split('>')) for s_info in response[3].split(';')
    ]

    print("NEIGHBOURS LIST:", Active_neighbours)
    print("STREAM LIST:")
    for stream in List_of_streams:
        print(" ->", stream.name)

    request_stream(List_of_streams[0].tag, socket)


    """
    This function receives messages from a socket and handles them based on their type.
    
    :param socket: The socket object used for communication
    """
def receive_m(socket):
    global Request_dict
    global Active_neighbours
    global OFF_flag

    while not OFF_flag.is_set():
        readable, _, _ = select.select([socket], [], [], 10)
        if readable:
            response, node_address = socket.recvfrom(BUFF_SIZE)
            print("Received:", response.decode())
            response = response.decode().split('|')
            if response[0] == 'C':
                control_message_handle(response, socket)
            elif response[0] == 'R':
                out = flood.request_r(
                    socket, response, node_address, Request_dict, Active_neighbours
                )
                print("Received well =", out)
        else:
            print(sys.stderr, 'timed out request to server.')


def request_stream(stream_ID, socket):
    """
    The function sends a request message to active neighbors for a given stream ID and updates the
    global request dictionary.
    
    :param stream_ID: The ID of the stream that is being requested
    :param socket: The socket parameter is a network socket object used for communication between the
    current host and other hosts on the network. It is used to send and receive data over the network
    """
    global Request_dict
    global Active_neighbours

    n = 8
    request_ID = ''.join(str(random.randint(0, 9)) for _ in range(n))
    print("REQUEST_ID:", request_ID)

    r = Request(request_ID, stream_ID, "Sent", host_ip)
    Request_dict[(request_ID, host_ip)] = r

    print(Active_neighbours)
    for req in Request_dict.values():
        print("Requests list member:", req.request_id, "|", req.stream_id, "|", req.state, "|", req.element)

    for neighbour in Active_neighbours:
        print("Sending to", neighbour)
        message = f'R|0|{r.request_id}|{r.stream_id}'
        socket.sendto(message.encode(), (neighbour, port))
        print("Sent", message, "bytes to", host_ip, ":", neighbour)


if __name__ == '__main__':
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    client_socket.bind((host_ip, port))
    send_join_request(client_socket)

    receiver_thread = threading.Thread(target=receive_m, args=(client_socket,))
    receiver_thread.start()

    leave = input("If you intend to leave type 'x'\n")
    if leave == "x":
        OFF_flag.set()
        for ip in Active_neighbours:
            requests_with_IP = [x for (_, k2), x in Request_dict.items() if k2 == ip]
            for req in requests_with_IP:
                client_socket.sendto(('R|2|' + req.request_id + '|' + req.stream_id).encode(), (ip, port))

    receiver_thread.join()
