import socket, threading, select
from helpers.class_objects import Node, Stream
from helpers.utils import BUFF_SIZE, off_flag, port,socket_address

node_dict = dict()
available_stream_list = []

def setup():
	"""
	The function reads a configuration file and creates nodes with tags and IP addresses, and adds
	neighbors to each node.
	"""
	global node_dict
	with open("./config/conf_file.txt") as f:
		for line in f:
			word = line.split(" ")
			if word[0] == "T":#TAG
				tag = line.split("\"")[1]
				node = Node(tag, word[1], word[3])
				node_dict[node.tag] = node
				node_dict[node.ip] = node
			elif word[0] == "V":#Vizinhos
				nodes = line.replace("\"", "").replace("\n", "")
				node_tags = nodes.split(" ")[1:]
				main_node = node_dict.get(node_tags[0])
				for node in node_tags[1:]:
					main_node.add_neighbour(node)


def receive_requests(controller_socket):
	"""
	This function receives requests from a controller socket and sends control responses based on the
	request type until an off flag is raised.
	
	:param controller_socket: The socket object used for communication with the controller
	"""
	global off_flag
	
	while off_flag == 0:
		r,_,_ = select.select([controller_socket],[],[], 0)
		if r:
			(message_rq, client_address) = controller_socket.recvfrom(BUFF_SIZE)
			request = message_rq.decode().split('|')
			match request[0]:
				case 'C':	#Control message
					control_response(controller_socket, client_address[0], request)

	controller_socket.close()


def control_response(controller_socket, user_ip, message_rq):
	"""
	This function generates a response message to a controller node based on the active neighbours and
	available streams, and sends it back to the same IP.
	
	:param controller_socket: The socket object used to communicate with the controller node
	:param user_ip: The IP address of the node that sent the message
	:param message_rq: The message_rq parameter is the message received from the node that triggered the
	control_response function. It is a list of strings that contains information about the message, such
	as the type of message and any additional data that may be included
	"""
	
	active_n_list = []
	message = 'C|0'

	#Find which node sent the message and set it as active
	node = node_dict.get(user_ip)
	if not node.is_active():
		node.activate()
		print(node.tag," is online")


	#Get a list of active neighbours related to the main node
	for neighbour in node.neighbours_list:
		n = node_dict.get(neighbour)
		if n.is_active():
			active_n_list.append(n.ip)

	#Add the list of active neighbours to the message so it can inform the main node
	if len(active_n_list)>0:	
		message += '|'
		for neighbour in active_n_list[:-1]:
			message += str(neighbour) + ';'
		message += str(active_n_list[-1])
	else:
		pass

	#Checks if node who sent the message is a Client
	#If it is a client then the available streams are also sent in the message
	match node.type:
		case "C":
			if len(available_stream_list)>0 and len(active_n_list)>0:
				print(available_stream_list)
				message += '|'
				for stream in available_stream_list:
					for _,value in stream.__dict__.items():
						message += value + '>'
					message = message[:-1]+';'
				message = message[:-1]
			else:
				print("Streams not yet available...", available_stream_list)
		case "S":
			#This serves as a space to include new info in the hello message response
			if message_rq[1] == '0' and len(message_rq)>2:
				for meta_info in message_rq[2:]:
					print(meta_info)
					stream_meta = meta_info.split(';')
					s = Stream(stream_meta[1],stream_meta[2],stream_meta[3],stream_meta[4], stream_meta[0])
					if not (any(x.tag is stream_meta[0] for x in available_stream_list)):
						available_stream_list.append(s)
						
	#Finnaly the message is sent as response to the same IP
	try:
		print("Sent message:",message)
		controller_socket.sendto(message.encode(), (user_ip, port))
	except Exception as e:
		print(e)
		raise Exception(e)


# This code block is the main entry point of the program. It creates a UDP socket, sets some socket
# options, binds the socket to a specific address, calls the `setup()` function to read a
# configuration file and create nodes with tags and IP addresses, and adds neighbors to each node. It
# then starts a thread to receive requests from the controller socket and sends control responses
# based on the request type until an off flag is raised. Finally, it prompts the user to input 'x' if
# they intend to leave, which sets the `off_flag` variable to 1 and terminates the program.
if __name__ == '__main__':

	controller_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	controller_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
	controller_socket.bind(socket_address)
	#network = input("Use overlay(o) or underlay(u) network?\n: ")
	setup()
	receiver_thread = threading.Thread(target = receive_requests, args = (controller_socket,))
	receiver_thread.start()
	leave = input("If you intend to leave type 'x'\n")
	if leave == "x":
		off_flag = 1