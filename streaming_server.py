import socket
import sched
import time
import threading
import select
import base64

import flooding_algorithm as flood
from class_objects import Stream, Request
from utils import BUFF_SIZE, host_ip, host_name, off_flag, port,socket_address

List_of_streams = []
Active_neighbours = []
Request_dict = dict() # ((Request_ID, origin_IP) : Request_OBJECT)

service_controller_ip = '10.0.1.10'

def introduction_server(socket, streams_available):
	hello_msg = 'C|0'
	
	for stream in streams_available:
		stream_meta = '|'+str(stream.tag)+';'+stream.name+';'+str(stream.fps)+';'+str(stream.max_delay)+';'+stream.type_of_data				
		hello_msg += stream_meta

	print("Sent : ",hello_msg)
	#print(service_controller_ip,port)
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

def generate_time_stream(socket, stream_ID, client_address):
	global off_flag
	# t = threading.Timer(1.0, send_time, args= [socket,stream_ID,client_address])
	# t.daemon = True
	# t.start()
	while off_flag == 0:
		s = sched.scheduler(time.time, time.sleep)
		event = s.enter(1, 1, send_time, argument = (socket, stream_ID, client_address, ))
		s.run()

	print("it did cancel\n")
	return 0

def send_time(socket, stream_ID, client_address):
	message = 'R|S|'
	t = time.strftime('%H:%M:%S', time.gmtime())
	#print(t, end="\r")
	message += stream_ID +'|'+ t
	print(message)
	socket.sendto(message.encode(),(client_address))

def handle_requests(socket):
	global off_flag
	global Request_dict
	global List_of_streams
	bag_of_threads = []

	while off_flag == 0:
		r,_,_ = select.select([socket],[],[], 0)
		if r:
			(rq, client_address) = socket.recvfrom(BUFF_SIZE)
			request = rq.decode()
			print("THIS is the Request ", request)
			request = request.split('|')
			#print(request)
			match request[0]:
				case 'C': # Received a control ('C') message
					if request[1] == '0':
						if len(request)>2:
							neighbour_list = request[2].split(';')
							for neighbour in neighbour_list:
								add_active_neighbour(neighbour)
						else:
							#print("There's not enough neighbours to initiate conversation")
							time.sleep(3)
							introduction_server(socket, List_of_streams)
				case 'R':
					print("Received request: ", rq.decode())
					out = flood.request_r(socket, request, client_address, Request_dict, Active_neighbours)
					print(out)
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
						print("Added a request")				
				case 'S':
					out = flood.request_r(socket, request, client_address, Request_dict, Active_neighbours)
					if out == 0:
						#generate_time_stream(socket, client_address)
						pass
	for thread in bag_of_threads:
		thread.join()
		#SEND request to relay servers of RQ


if __name__ == '__main__':


	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFF_SIZE)
	server_socket.bind(socket_address)
	print('Running Stream server on ', server_socket.getsockname())

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
	
	leave = input("If you intend to leave type 'x'\n")
	if leave == "x":
		print("Leaving...")
		off_flag = 1

	receiver_thread.join()