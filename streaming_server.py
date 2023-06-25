import socket
import sched
import time
import threading
import select

import flooding_algorithm as flood
from class_objects import Stream, Request
from utils import host_ip, socket_address, off_flag, BUFF_SIZE


print("Streaming Server info:", socket_address)
List_of_streams = []
Active_neighbours = []
Request_dict = {}  # ((Request_ID, origin_IP): Request_OBJECT)

service_controller_ip = '10.0.1.10'


def introduction_server(socket, streams_available):
    """
    The function sends a hello message with stream metadata to a server using a socket.
    
    :param socket: The socket parameter is a network socket object that is used to establish a
    connection with a remote server or client. It is used to send and receive data over the network
    :param streams_available: A list of available streams that can be sent over the socket connection.
    Each stream is represented by an object that contains metadata such as the stream's tag, name,
    frames per second (fps), maximum delay, and type of data
    """
    hello_msg = 'C|0'

    for stream in streams_available:
        stream_meta = f'|{stream.tag};{stream.name};{stream.fps};{stream.max_delay};{stream.type_of_data}'
        hello_msg += stream_meta

    print("Sent:", hello_msg)
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


def generate_time_stream(socket, stream_ID, client_address):
    """
    This function generates a time stream by repeatedly calling the send_time function with a delay of 1
    second, until a global off_flag is set to 1.
    
    :param socket: The socket parameter is likely a network socket object that is used to send and
    receive data over a network connection. It is probably used in the send_time function to send time
    data to the client at the specified client_address
    :param stream_ID: The stream_ID parameter is a unique identifier for the time stream being
    generated. It is used to differentiate between multiple time streams that may be running
    simultaneously
    :param client_address: The client_address parameter is likely the address of the client that the
    time stream is being generated for. This could be an IP address or a hostname
    :return: an integer value of 0.
    """
    global off_flag

    while off_flag == 0:
        s = sched.scheduler(time.time, time.sleep)
        event = s.enter(1, 1, send_time, argument=(socket, stream_ID, client_address))
        s.run()

    print("Cancelled\n")
    return 0


def send_time(socket, stream_ID, client_address):
    """
    The function sends a message containing the current time and a stream ID to a specified client
    address using a socket.
    
    :param socket: The socket object is used to establish a network connection and send/receive data
    over the network
    :param stream_ID: The stream ID is a unique identifier for a particular stream of data being sent
    over the network. It is used to distinguish between different streams of data that may be sent or
    received by the system
    :param client_address: The client_address parameter is a tuple containing the IP address and port
    number of the client that the message will be sent to. It is used as the second argument in the
    socket.sendto() method to specify the destination of the message
    """
    message = 'R|S|'
    t = time.strftime('%H:%M:%S', time.gmtime())
    message += f'{stream_ID}|{t}'
    print(message)
    socket.sendto(message.encode(), (client_address))


def handle_requests(socket):
    """
    This function handles incoming requests on a socket and performs actions based on the type of
    request received.
    
    :param socket: The socket object used for communication
    """
    global off_flag
    global Request_dict
    global List_of_streams
    bag_of_threads = []

    while off_flag == 0:
        r, _, _ = select.select([socket], [], [], 0)
        if r:
            rq, client_address = socket.recvfrom(BUFF_SIZE)
            request = rq.decode()
            print("Request:", request)
            request = request.split('|')
            if request[0] == 'C':  # Received a control ('C') message
                if request[1] == '0':
                    if len(request) > 2:
                        neighbour_list = request[2].split(';')
                        for neighbour in neighbour_list:
                            add_active_neighbour(neighbour)
                    else:
                        time.sleep(3)
                        introduction_server(socket, List_of_streams)
            elif request[0] == 'R':
                print("Received request:", rq.decode())
                out = flood.request_r(socket, request, client_address, Request_dict, Active_neighbours)
                print(out)
                if out != 0:
                    if out[0] == "stream":
                        for stream in List_of_streams:
                            if stream.tag == out[1]:
                                stream_thread = threading.Thread(target=generate_time_stream,
                                                                 args=(socket, out[1], client_address))
                                stream_thread.start()
                                bag_of_threads.append(stream_thread)
                    elif out[0] == "cancel":
                        print("CANCELLED")
                        off_flag = 1
                else:
                    print("Added a request")
            elif request[0] == 'S':
                out = flood.request_r(socket, request, client_address, Request_dict, Active_neighbours)
                if out == 0:
                    pass

    for thread in bag_of_threads:
        thread.join()


if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    server_socket.bind(socket_address)
    print('Running Stream server on', server_socket.getsockname())

    time_stream = Stream("time", 1, 0.5, "text", "1")
    sound_stream = Stream("music", 10000, 0.1, "sound", "2")

    List_of_streams.append(time_stream)
    List_of_streams.append(sound_stream)

    Request_dict[("0", host_ip)] = Request("0", time_stream.tag, "Active Retransmission", host_ip)
    Request_dict[("1", host_ip)] = Request("1", sound_stream.tag, "Active Retransmission", host_ip)
    print("Time tag:", time_stream.tag)
    print("Song tag:", sound_stream.tag)

    introduction_server(server_socket, List_of_streams)

    receiver_thread = threading.Thread(target=handle_requests, args=(server_socket,))
    receiver_thread.start()

    leave = input("If you intend to leave, type 'x'\n")
    if leave == "x":
        print("Leaving...")
        off_flag = 1

    receiver_thread.join()
