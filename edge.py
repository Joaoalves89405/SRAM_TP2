import socket
import time
import threading
import select

import helpers.flooding_algorithm as flood
from helpers.utils import BUFF_SIZE, off_flag, port,socket_address

List_of_streams = []
Active_neighbours = []
Request_dict = dict()

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
	The function adds a neighbour to a list of active neighbours and checks if the neighbour is already
	in the list.
	
	:param neighbour: The parameter "neighbour" is a variable that represents a neighboring object or
	entity in a system or network. The function "add_active_neighbour" adds this neighbor to a list of
	active neighbors called "Active_neighbours". If the neighbor is already in the list, the function
	prints a message indicating
	"""
	global Active_neighbours

	if neighbour not in Active_neighbours:	
		Active_neighbours.append(neighbour)
	else:
		print("Neighbour already active : please check the request")

def handle_requests(socket):
	"""
	This is a Python function that handles incoming requests on a socket and performs actions based on
	the type of request received.
	
	:param socket: The socket object used for communication
	"""
	global off_flag
	global Request_dict
	
	while off_flag == 0:
		r,_,_ = select.select([socket],[],[], 0)
		if r:
			(rq, peer_address) = socket.recvfrom(BUFF_SIZE)
			print("THIS is the Request ", rq.decode())
			request = rq.decode().split('|')

			match request[0]:
				case 'C':
					if request[1] == '0':
						if len(request)>2:
							neighbour_list = request[2].split(';')
							for neighbour in neighbour_list:
								add_active_neighbour(neighbour)
						else:
							print("There's not enough neighbours to initiate conversation")
							time.sleep(3)
							introduction_server(socket)
				case 'R':
					out = flood.request_r(socket, request, peer_address, Request_dict, Active_neighbours)
				

# This code block is the main function of the program. It creates a UDP socket, sets its buffer size,
# binds it to a specific address, and starts a thread to handle incoming requests. It also sends an
# introduction message to a service controller and waits for user input to leave the program. If the
# user inputs 'x', it sends a leave message to all active neighbors and sets a flag to stop the
# program. Finally, it waits for the receiver thread to finish before exiting.
if __name__ == '__main__':

	edge_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	edge_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
	edge_socket.bind(socket_address)
	print('Running edge on ', edge_socket.getsockname())

	introduction_server(edge_socket)
	receiver_thread = threading.Thread(target = handle_requests, args = (edge_socket,))
	receiver_thread.start()

	leave = input("If you intend to leave type 'x'\n")
	if leave == "x":
		print("Leaving...")
		for ip in Active_neighbours:
			requests_with_IP = [x for (_,k2), x in Request_dict.items() if k2 == ip]
			for req in requests_with_IP:
				edge_socket.sendto(('R|2|'+req.request_id+'|'+req.stream_id).encode(), (ip,port))

		off_flag = 1

	receiver_thread.join()