import socket
import threading
import select
from class_objects import Node, Stream
from utils import host_ip, socket_address, off_flag, BUFF_SIZE


# Socket Create
print("LISTENING AT:", socket_address)
node_dict = {}
available_stream_list = []

def setup():
	"""
	The function reads a configuration file and creates nodes with their respective neighbors based on
	the information in the file.
	"""
	global node_dict
	with open("conf_file.txt") as f:
		for line in f:
			word = line.split()
			if word[0] == "T": # TAG
				tag = line.split("\"")[1]
				node = Node(tag, word[1], word[3])
				node_dict[node.tag] = node
			elif word[0] == "V": # Vizinhos
				nodes = line.replace("\"", "").rstrip()
				node_tags = nodes.split(" ")[1:]
				main_node = node_dict.get(node_tags[0])
				for node in node_tags[1:]:
					main_node.add_neighbour(node)

def receive_requests(controller_socket):
	"""
	This function receives requests from a controller socket and sends control responses based on the
	request type.
	
	:param controller_socket: The socket object used for communication with the controller
	"""
	global off_flag
	
	while off_flag == 0:
		r, _, _ = select.select([controller_socket], [], [], 0)
		if r:
			message_rq, client_address = controller_socket.recvfrom(BUFF_SIZE)
			request = message_rq.decode().split('|')
			if request[0] == 'C':  # Control message
				control_response(controller_socket, client_address[0], request)

	controller_socket.close()

def control_response(controller_socket, user_ip, message_rq):
	"""
	The function `control_response` prepares and sends a response message to a node based on its type
	and message request.
	
	:param controller_socket: The socket object used to communicate with the controller
	:param user_ip: The IP address of the node that sent the message
	:param message_rq: The message_rq parameter is a list containing the message received from a node.
	The first element of the list indicates the type of message (e.g. 'C' for control message, 'S' for
	stream message), and the following elements contain any additional information related to the
	message
	"""
	active_n_list = []
	message = 'C|0'  # Prepare a response message, 'C' for control message and '0' for Hello

	node = node_dict.get(user_ip)  # Find which node sent the message and set it as active
	if not node.is_active():
		node.activate()
		print(node.tag, "is online")

	for neighbour in node.neighbours_list:  # Get a list of active neighbours related to the main node
		n = node_dict.get(neighbour)
		if n.is_active():
			active_n_list.append(n.ip)

	if len(active_n_list) > 0:	
		message += '|' + ';'.join(active_n_list)  # Add the list of active neighbours to the message
	else:
		pass

	if node.type == "C":  # Checks if node who sent the message is a Client
		if len(available_stream_list) > 0 and len(active_n_list) > 0:
			message += '|' + ';'.join([str(stream) for stream in available_stream_list])
		else:
			print("Streams not yet available...", available_stream_list)
	elif node.type == "S":
		if message_rq[1] == '0' and len(message_rq) > 2:  # This serves as a space to include new info in the hello message response
			for meta_info in message_rq[2:]:
				print(meta_info)
				stream_meta = meta_info.split(';')
				s = Stream(*stream_meta)
				if not any(x.tag == stream_meta[0] for x in available_stream_list):
					available_stream_list.append(s)

	try:
		print("Sent message:", message)
		controller_socket.sendto(message.encode(), (user_ip, port))
	except Exception as e:
		print(e)
		raise Exception(e)


if __name__ == '__main__':
	controller_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	controller_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
	controller_socket.bind(socket_address)
	setup()
	receiver_thread = threading.Thread(target=receive_requests, args=(controller_socket,))
	receiver_thread.start()
	leave = input("If you intend to leave type 'x'\n")
	if leave == "x":
		off_flag = 1

	# receiver_thread.join()
