import socket
import sched
import time
import threading
import select

import helpers.flooding_algorithm as flood
from helpers.class_objects import Stream, Request
from helpers.utils import BUFF_SIZE, host_ip, off_flag, port,socket_address

List_of_streams = []
Active_neighbours = []
Request_dict = dict() 

service_controller_ip = '10.0.1.10'

def introduction_server(socket, streams_available):
	"""
	This function sends a hello message to a service controller with information about available
	streams.
	
	:param socket: The socket parameter is a network socket object that is used to send data over the
	network. It is typically created using the socket library in Python
	:param streams_available: streams_available is a list of available streams that can be accessed
	through the socket. Each stream in the list contains metadata such as its tag, name, frames per
	second (fps), maximum delay, and type of data. The function creates a hello message that includes
	this metadata for each stream and sends it
	"""
	hello_msg = 'C|0'
	
	for stream in streams_available:
		stream_meta = '|'+str(stream.tag)+';'+stream.name+';'+str(stream.fps)+';'+str(stream.max_delay)+';'+stream.type_of_data				
		hello_msg += stream_meta

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

def generate_time_stream(socket, stream_ID, client_address):
	"""
	This function generates a time stream by repeatedly scheduling the sending of time to a client
	address through a socket until a flag is set to turn it off.
	
	:param socket: The socket object is used to establish a network connection between the server and
	the client. It is used to send and receive data over the network
	:param stream_ID: The stream_ID parameter is a unique identifier for the time stream being
	generated. It is used to differentiate between multiple time streams that may be running
	simultaneously
	:param client_address: The client_address parameter is likely the address of the client that is
	receiving the time stream. It could be an IP address or a hostname
	:return: an integer value of 0.
	"""
	global off_flag
	while off_flag == 0:
		s = sched.scheduler(time.time, time.sleep)
		event = s.enter(1, 1, send_time, argument = (socket, stream_ID, client_address, ))
		s.run()

	print("it did cancel\n")
	return 0

def send_time(socket, stream_ID, client_address):
	"""
	This function sends the current time to a client through a socket connection with a specified stream
	ID and client address.
	
	:param socket: The socket object used for communication
	:param stream_ID: The stream ID is a unique identifier for a particular stream of data being
	transmitted over the network. It is used to distinguish between different streams of data and ensure
	that they are delivered to the correct destination. In this function, the stream ID is passed as a
	parameter and is included in the message that is
	:param client_address: The client_address parameter is the address of the client that the message
	will be sent to. It is a tuple containing the IP address and port number of the client
	"""
	message = 'R|S|'
	t = time.strftime('%H:%M:%S', time.gmtime())
	message += stream_ID +'|'+ t
	print("Sended streamID: ",stream_ID," with payload ", t, " to ",client_address)
	socket.sendto(message.encode(),(client_address))

def handle_requests(socket):
	"""
	This function handles incoming requests on a socket, processes them, and spawns threads to generate
	time streams if necessary.
	
	:param socket: The socket object used for communication
	"""
	global off_flag
	global Request_dict
	global List_of_streams
	bag_of_threads = []

	while off_flag == 0:
		r,_,_ = select.select([socket],[],[], 0)
		if r:
			(rq, client_address) = socket.recvfrom(BUFF_SIZE)
			request = rq.decode()
			request = request.split('|')
			match request[0]:
				case 'C': 
					print("Control message received: ", request)
					if request[1] == '0':
						if len(request)>2:
							neighbour_list = request[2].split(';')
							for neighbour in neighbour_list:
								add_active_neighbour(neighbour)
						else:
							time.sleep(3)
							introduction_server(socket, List_of_streams)
				case 'R':
					print("Request received: ", rq.decode())
					out = flood.request_r(socket, request, client_address, Request_dict, Active_neighbours)
					if out != 0:
						if out[0] == "stream":
							for stream in List_of_streams:
								if stream.tag == out[1]:
									stream_thread = threading.Thread(target = generate_time_stream, args = (socket, out[1], client_address,))
									stream_thread.start()
									bag_of_threads.append(stream_thread)
						elif out[0] == "cancel":
							print("CANCELLED")
							off_flag = 1
					else:
						print("Request added to the queue")				
				case 'S':
					out = flood.request_r(socket, request, client_address, Request_dict, Active_neighbours)
					if out == 0:
						pass
	for thread in bag_of_threads:
		thread.join()


# The `if __name__ == '__main__':` block is a conditional statement that checks if the current script
# is being run as the main program. If it is, then it executes the code within the block. This is a
# common Python idiom used to ensure that certain code is only executed when the script is run
# directly, and not when it is imported as a module by another script. In this specific code, it
# initializes the server socket, creates two streams, adds them to a list of streams, creates two
# requests and adds them to a dictionary, calls the `introduction_server` function to send a hello
# message to a service controller, starts a thread to handle incoming requests, and waits for user
# input to exit the program.
if __name__ == '__main__':


	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
	server_socket.bind(socket_address)

	time_stream = Stream("time",1,0.5,"text", "1")
	sound_stream = Stream("music",10000,0.1,"sound","2")
	
	List_of_streams.append(time_stream)
	List_of_streams.append(sound_stream)

	Request_dict[("0", host_ip)] = Request("0", time_stream.tag, "Active Retransmission", host_ip)
	Request_dict[("1", host_ip)] = Request("1", sound_stream.tag, "Active Retransmission", host_ip)
	print("Time tag : ", time_stream.tag)
	print("Song tag : ", sound_stream.tag)

	introduction_server(server_socket, List_of_streams)

	receiver_thread = threading.Thread(target = handle_requests, args = (server_socket,))
	receiver_thread.start()
	
	leave = input("Press 'x' to leave\n")
	if leave == "x":
		off_flag = 1

	receiver_thread.join()