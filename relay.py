import socket
import time
import threading
import select

import flooding_algorithm as flood
from utils import host_ip, socket_address, off_flag, BUFF_SIZE


List_of_streams = []
Active_neighbours = []
Request_dict = {}  # ((Request_ID, origin_IP): Request_OBJECT)

service_controller_ip = '10.0.1.10'


def introduction_server(socket):
    """
    This function sends a "hello" message to a server using a socket.
    
    :param socket: The `socket` parameter is a socket object that represents a network connection
    between two endpoints. It is used to send and receive data over the network. In this case, it is
    used to send a hello message to a service controller at a specific IP address and port
    """
    hello_msg = 'C|0|'
    try:
        socket.sendto(hello_msg.encode(), (service_controller_ip, port))
    except Exception as e:
        raise e


def add_active_neighbour(neighbour):
    """
    The function adds a neighbour to a list of active neighbours if it is not already in the list.
    
    :param neighbour: The parameter "neighbour" is a variable that represents a neighboring object or
    entity that is being added to a list of active neighbors. The function "add_active_neighbour" checks
    if the neighbor is already in the list of active neighbors and adds it to the list if it is not
    already present
    """
    global Active_neighbours

    if neighbour not in Active_neighbours:
        Active_neighbours.append(neighbour)
    else:
        print("Neighbour already active: please check the request")


def handle_requests(socket):
    """
    The function handles incoming requests from a socket and performs actions based on the type of
    request received.
    
    :param socket: The socket parameter is a network socket object that is used to send and receive data
    over the network. It is used to communicate with other nodes in the network
    """
    global off_flag
    global Request_dict

    while off_flag == 0:
        r, _, _ = select.select([socket], [], [], 0)
        if r:
            rq, peer_address = socket.recvfrom(BUFF_SIZE)
            request = rq.decode().split('|')

            match request[0]:
                case 'C':
                    if request[1] == '0':
                        if len(request) > 2:
                            neighbour_list = request[2].split(';')
                            for neighbour in neighbour_list:
                                add_active_neighbour(neighbour)
                        else:
                            print("There's not enough neighbours to initiate conversation")
                            time.sleep(3)
                            introduction_server(socket)
                case 'R':
                    out = flood.request_r(socket, request, peer_address, Request_dict, Active_neighbours)


if __name__ == '__main__':
    relay_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    relay_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    relay_socket.bind(socket_address)

    print('Running Relay element on', relay_socket.getsockname())

    introduction_server(relay_socket)

    receiver_thread = threading.Thread(target=handle_requests, args=(relay_socket,))
    receiver_thread.start()

    leave = input("If you intend to leave, type 'x'\n")
    if leave == "x":
        for ip in Active_neighbours:
            requests_with_IP = [x for (_, k2), x in Request_dict.items() if k2 == ip]
            for req in requests_with_IP:
                relay_socket.sendto(('R|2|' + req.request_id + '|' + req.stream_id).encode(), (ip, port))

        print("Leaving...")
        off_flag = 1

    receiver_thread.join()
