import socket
import select
import sys
import threading
import random

from helpers.class_objects import Request, Stream
import helpers.flooding_algorithm as flood
from helpers.utils import BUFF_SIZE, host_ip, off_flag, port

TIMEOUT = 3
List_of_streams = []
Active_neighbours = []
Request_dict = dict()

service_controller_ip = '10.0.1.10'
port = 9090

def send_join_request(socket):
	"""
	This function sends a join request message to a specified IP address and port using a socket.
	
	:param socket: The socket parameter is a reference to a socket object that is used to send the join
	request message to a server. A socket is a communication endpoint that allows two processes to
	communicate with each other over a network. In this case, the socket is used to send a message to a
	server at a specific
	"""
	message = 'C|0|'
	socket.sendto(message.encode(), (service_controller_ip, port))

def control_message_handle(response,socket):
	"""
	The function handles control messages by updating the list of active neighbours and list of streams,
	and then requests a stream.
	
	:param response: The response parameter is a list containing information received from a control
	message. The information includes the type of message, the sender's ID, a list of active neighbours,
	and a list of available streams
	:param socket: The "socket" parameter is likely a reference to a network socket object, which is
	used to establish a connection and exchange data with another computer or device over a network. In
	this context, it is probably being used to send and receive messages related to a streaming
	application
	"""
	global Active_neighbours
	global List_of_streams

	Active_neighbours = list(response[2].split(';'))
	List_of_streams = list(response[3].split(';'))
	for i in range(len(List_of_streams)):
		s_info = List_of_streams[i].split('>')
		s = Stream(s_info[1], s_info[2], s_info[3], s_info[4], s_info[0])
		List_of_streams[i] = s
	
	print("List of neighbours: ", Active_neighbours)
	print("Streams available : ")
	for stream in List_of_streams:
		print(stream.name)
	print("Requesting stream: ", List_of_streams[0].name)
	request_stream(List_of_streams[0].tag, socket)
		


def receive_m(socket):
	"""
	This function receives messages from a socket and handles them based on their type.
	
	:param socket: The socket object used for communication with other nodes in the network
	"""
	global Request_dict
	global Active_neighbours
	global off_flag
	
	while off_flag == 0:
		pass
		readable,_,_ = select.select([socket],[],[], 10)
		if readable:
			response, node_address = socket.recvfrom(BUFF_SIZE)
			response = response.decode().split('|')
			print("response", response)
			match response[0]:
				case 'C':
					control_message_handle(response, socket)
				case 'R':
					out = flood.request_r(socket, response, node_address, Request_dict, Active_neighbours)
					#print("Received well = ",out)
			
		else:
			print('Request timed out')

def request_stream(stream_ID, socket):
	"""
	The function sends a request for a stream to active neighbors using a randomly generated request ID
	and adds the request to a dictionary.
	
	:param stream_ID: The ID of the stream being requested
	:param socket: The socket parameter is a network socket object used for communication between the
	client and server. It is used to send and receive data over the network
	"""
	global Request_dict
	global Active_neighbours
	n = 8
	request_ID = ''
	for _ in range(n):
		a = str(random.randint(0,9)) 
		request_ID+=a
	r = Request(request_ID, stream_ID, "Sent", host_ip)
	Request_dict[request_ID,host_ip] = r
		
	for neighbour in Active_neighbours:
		print("Sending payload: ", 'R|0|'+r.request_id+'|'+r.stream_id, "to ",neighbour)
		socket.sendto(('R|0|'+r.request_id+'|'+r.stream_id).encode(), (neighbour, port))

# This code block is the main function of the program. It creates a UDP socket, sets the buffer size,
# binds the socket to a host IP and port, sends a join request to a service controller, starts a
# thread to receive messages, prompts the user to input 'x' if they intend to leave, and if so, sets a
# flag to indicate the program should stop running and sends a leave message to all active neighbors.
# Finally, it waits for the receiver thread to finish before exiting the program.
if __name__ == '__main__':
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    client_socket.bind((host_ip, port))
    send_join_request(client_socket)
    receiver_thread = threading.Thread(target=receive_m, args=(client_socket,))
    receiver_thread.start()
    leave = input("Press 'x' to leave\n")
    if leave == "x":
        off_flag = 1
        for ip in Active_neighbours:
            requests_with_IP = [x for (_, k2), x in Request_dict.items() if k2 == ip]
            for req in requests_with_IP:
                client_socket.sendto(('R|2|' + req.request_id + '|' + req.stream_id).encode(), (ip, port))
    receiver_thread.join()
