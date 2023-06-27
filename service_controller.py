import socket, threading, select
from helpers.class_objects import Node, Stream
from helpers.utils import BUFF_SIZE, off_flag, port,socket_address

# Socket Create
node_dict = dict()
available_stream_list = []

def setup():
	global node_dict
	with open("./config/conf_file.txt") as f:
		for line in f:
			word = line.split(" ")
			if word[0] == "T":#TAG
				tag = line.split("\"")[1]
				node = Node(tag, word[1], word[3])
				node_dict[node.tag] = node
				node_dict[node.ip] = node
				#print(node_dict)
			elif word[0] == "V":#Vizinhos
				nodes = line.replace("\"", "").replace("\n", "")
				node_tags = nodes.split(" ")[1:]
				#print("This the node tag we are searching for ",node_tags)
				main_node = node_dict.get(node_tags[0])
				for node in node_tags[1:]:
					main_node.add_neighbour(node)
	#print(len(node_dict))

def function():
	pass

def receive_requests(controller_socket):
	global off_flag
	
	while off_flag == 0:
		r,_,_ = select.select([controller_socket],[],[], 0)
		if r:
			(message_rq, client_address) = controller_socket.recvfrom(BUFF_SIZE)
			#print("THIS is the Helllo message :", message_rq.decode(), "From: ", client_address[0])
			request = message_rq.decode().split('|')
			match request[0]:
				case 'C':	#Control message
					control_response(controller_socket, client_address[0], request)

	controller_socket.close()


def control_response(controller_socket, user_ip, message_rq):
	
	active_n_list = []
	#Prepare a response message, 'C' for control message and '0' for Hello 
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
		pass#print("Less than one active neighbour for ", node.tag,". List: ", active_n_list)		

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
				#print("Stream available received: ", message_rq[2:] )
				for meta_info in message_rq[2:]:
					print(meta_info)
					stream_meta = meta_info.split(';')
					s = Stream(stream_meta[1],stream_meta[2],stream_meta[3],stream_meta[4], stream_meta[0])
					if not (any(x.tag is stream_meta[0] for x in available_stream_list)):
						available_stream_list.append(s)
						
			#print("STREAM LIST: ", available_stream_list)
	#Finnaly the message is sent as response to the same IP
	try:
		print("Sent message:",message)
		controller_socket.sendto(message.encode(), (user_ip, port))
	except Exception as e:
		print(e)
		raise Exception(e)





if __name__ == '__main__':


	controller_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	controller_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
	controller_socket.bind(socket_address)
	#network = input("Use overlay(o) or underlay(u) network?\n: ")
	#print(controller_socket)
	setup()
	#e1_nlist = node_dict.get("E1").get_neighbours_list()
	#print(e1_nlist)
	receiver_thread = threading.Thread(target = receive_requests, args = (controller_socket,))
	receiver_thread.start()
	leave = input("If you intend to leave type 'x'\n")
	if leave == "x":
		off_flag = 1

	#receiver_thread.join()