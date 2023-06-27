import socket
import sched
import time
import threading
import select
import base64

import flooding_algorithm as flood
from class_objects import Request


host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print(host_ip)
port = 9090
socket_address = (host_ip, port)
off_flag = 0
BUFF_SIZE = 65536

List_of_streams = []
Active_neighbours = []
Request_dict = dict() # ((Request_ID, origin_IP) : Request_OBJECT)

service_controller_ip = '10.0.1.10'

def introduction_server(socket):
	hello_msg = 'C|0|'
	try:
		socket.sendto(hello_msg.encode(), (service_controller_ip, port))
	except Exception as e:
		raise e

def add_active_neighbour(neighbour):
	global Active_neighbours

	if neighbour not in Active_neighbours:	
		Active_neighbours.append(neighbour)
	else:
		print("Neighbour already active : please check the request")

def handle_requests(socket):
	global off_flag
	global Request_dict
	
	while off_flag == 0:
		r,_,_ = select.select([socket],[],[], 0)
		if r:
			(rq, peer_address) = socket.recvfrom(BUFF_SIZE)
			print("THIS is the Request ", rq.decode())
			request = rq.decode().split('|')
			# if len(Request_dict.values())>0:
			# 	for req in Request_dict.values():
			# 		print("Stored: ",req.request_id," from", req.element)

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
				

if __name__ == '__main__':


	edge_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	edge_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
	edge_socket.bind(socket_address)
	#network = input("Use overlay(o) or underlay(u) network?\n: ")
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