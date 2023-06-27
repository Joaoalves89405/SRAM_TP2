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
Request_dict = dict() # ((Request_ID, origin_IP) : Request_OBJECT)

service_controller_ip = '10.0.1.10'
port = 9090

def send_join_request(socket):
	message = 'C|0|'
	bytes_sent = socket.sendto(message.encode(), (service_controller_ip, port))

def control_message_handle(response,socket):
	global Active_neighbours
	global List_of_streams

	Active_neighbours = list(response[2].split(';'))
	List_of_streams = list(response[3].split(';'))
	for i in range(len(List_of_streams)):
		s_info = List_of_streams[i].split('>')
		s = Stream(s_info[1], s_info[2], s_info[3], s_info[4], s_info[0])
		List_of_streams[i] = s
	
	print("NEIGHBOURS LIST :", Active_neighbours)
	print("STREAM LIST :")
	for stream in List_of_streams:
		print(" ->", stream.name)

	request_stream(List_of_streams[0].tag, socket)
		


def receive_m(socket):
	global Request_dict
	global Active_neighbours
	global off_flag
	
	while off_flag == 0:
		pass
		readable,_,_ = select.select([socket],[],[], 10)
		if readable:
			response, node_address = socket.recvfrom(BUFF_SIZE)
			print("Received:",response.decode())
			response = response.decode().split('|')
			match response[0]:
				case 'C':
					control_message_handle(response, socket)
				case 'R':
					out = flood.request_r(socket, response, node_address, Request_dict, Active_neighbours)
					print("Received well = ",out)
			
		else:
			print(sys.stderr, 'timed out request to server.')

def request_stream(stream_ID, socket):
	global Request_dict
	global Active_neighbours
	n = 8
	request_ID = ''
	print("Requesting stream")
	for _ in range(n):
		a = str(random.randint(0,9)) 
		request_ID+=a
	print("REQUEST_ID:",request_ID)
	r = Request(request_ID, stream_ID, "Sent", host_ip)
	Request_dict[request_ID,host_ip] = r
	print(Active_neighbours)
	for req in Request_dict.values():
		print("Requests list member:",  req.request_id,"|", req.stream_id,"|", req.state,"|" ,req.element)
		
	for neighbour in Active_neighbours:
		print("Sending to ", neighbour)
		bytes_sent = socket.sendto(('R|0|'+r.request_id+'|'+r.stream_id).encode(), (neighbour, port))
		print("Sent ", 'R|0|'+r.request_id+'|'+r.stream_id, " bytes to ", host_ip,":",neighbour)

if __name__ == '__main__':
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
    client_socket.bind((host_ip, port))

    # res = input("\nEnter room: \n1) Nature \n2) Action \n3) Horror \n4) Animation \n : ")
    send_join_request(client_socket)
    receiver_thread = threading.Thread(target=receive_m, args=(client_socket,))
    receiver_thread.start()
    leave = input("If you intend to leave type 'x'\n")
    if leave == "x":
        off_flag = 1
        for ip in Active_neighbours:
            requests_with_IP = [x for (_, k2), x in Request_dict.items() if k2 == ip]
            for req in requests_with_IP:
                client_socket.sendto(('R|2|' + req.request_id + '|' + req.stream_id).encode(), (ip, port))
    receiver_thread.join()
