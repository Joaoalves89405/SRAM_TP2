import socket
import time
import threading
from helpers.class_objects import Stream, Request

def request_r(socket, request, origin_address, request_dict, neighbours_list):
	type_of_message = request[1]

	match type_of_message:
		case '0':
			req_ID = request[2]
			stream_ID = request[3]

			requests_with_id = [x for (k1,_), x in request_dict.items() if k1 == req_ID]
			if len(requests_with_id) > 0:
				if any(x.element is origin_address for x in requests_with_id):
					print("It exists an request from this IP:")
				else :
					print("There isnt any request from that element")
					socket.sendto(('R|2|'+req_ID+'|'+stream_ID).encode(), origin_address)
			else:
				
				if any(str(x.stream_id) == str(stream_ID) and x.state == "Active Retransmission" for x in request_dict.values()):
					for req in request_dict.values():
						#checks if it has an active retransmission
						# of the desired stream
						if req.state == "Active Retransmission" and str(req.stream_id) == str(stream_ID):
							print("Sent Confirmation for stream -> ",req.stream_id )
							socket.sendto(('R|1|'+req_ID).encode(), origin_address)
							rq_obj =  Request(req_ID, stream_ID, "Answered", origin_address[0])
				#Adds the request to the list
				#In case there is a timeout it adds it too
				else:	
					if len(request)>4:
						rq_obj =  Request(req_ID, stream_ID, "Received", origin_address[0], request[4])
					else:
						rq_obj =  Request(req_ID, stream_ID, "Received", origin_address[0])
						print("ADDED Request : ", rq_obj.__dict__.values())	
					for neighbour in [x for x in neighbours_list if x != origin_address[0]]:
						message = '|'.join(request)
						socket.sendto(message.encode(), (neighbour, 9090))
						rq_obj1 = Request(req_ID, stream_ID, "Sent", neighbour)
						print("New requests sent",rq_obj1.__dict__.values())
						request_dict[req_ID, neighbour] = rq_obj1
				request_dict[req_ID, origin_address[0]] = rq_obj

			return 0
		case '1':
			req_ID = request[2]
			requests_with_id = [x for (k1,_), x in request_dict.items() if k1 == req_ID]
			for x in requests_with_id:
				#print("requests_with_id:", x.element)
				pass
			if any(x.element == origin_address[0] for x in requests_with_id):
				rq_obj = request_dict.get((req_ID, origin_address[0]))
				print(rq_obj)
				if rq_obj.state == "Sent":
					socket.sendto(('R|1|'+req_ID).encode(), origin_address)
					print("Sent a Confirmation to: ", origin_address[0], "\nThis was the message: ", 'R|1|'+req_ID)
					rq_obj.change_state("C")
				elif rq_obj.state == "Answered":
					rq_obj.change_state("AR")
					return ("stream", rq_obj.stream_id)
					#Returns the stream id so it may be transmitted on the node
			elif (x.element == socket.getsockname()[0] for x in requests_with_id):
				rq_obj = request_dict.get((req_ID,socket.getsockname()[0]))
				print(rq_obj)
				if rq_obj.state == "Sent":
					socket.sendto(('R|1|'+req_ID).encode(), origin_address)
					print("Sent a Confirmation to: ", origin_address[0], "\nThis was the message: ", 'R|1|'+req_ID)
					rq_obj.change_state("C")

		case '2':
			req_ID = request[2]
			stream_ID = request[3]
			real_request=[]

			requests_with_id = [x for (k1,_), x in request_dict.items() if k1 == req_ID]
			for request in request_dict.values():
				#print(request.__dict__.values())
				pass
			for req in requests_with_id:
				#print("Requests Available to cancel:", req.request_id, "element:",req.element, "state:",req.state)
				if req.state == "Sent" or req.state == "Active Retransmission" or req.state == "Confirmed":
					#print("Requests with state sent or Active Retransmission:", req.element)
					#print(origin_address)
					if req.element != origin_address[0]:
						#print("Sent request to cancel to ", req.element)
						socket.sendto(('R|2|'+req_ID+'|'+stream_ID).encode(), (req.element,9090))
				ret = request_dict.pop((req.request_id, req.element))
			for requ in request_dict.values():
				if len(requ.request_id)==8:
					real_request.append(requ)
					#print("Requests that are real :",requ.__dict__.values())
			if not any(x.stream_id == stream_ID for x in real_request):
				#print("Received notice to cancel")
				return ("cancel", stream_ID)
			return 0
		case 'S':
			stream_ID = request[2]
			stream_content = request[3:]
			print("This is the stream content:", stream_content[0])
			print("Streaming TIME : ", request[2])
			for req in request_dict.values():
				print("LIST OF REQUESTS entry:", req.request_id,"|", req.stream_id,"|", req.state,"|" ,req.element)
				#print("req ID : ", req.stream_id, " Looking for : ", stream_ID)
				if req.stream_id == stream_ID :
					#print("req_streamid == streamID : ", req.stream_id)
					if req.state == "Received":
						print("req_state == received : ", req.state)
						socket.sendto(('R|1|'+req.request_id).encode(), (req.element,9090))
						req.change_state("A")
					elif req.state == "Sent":
						print("Request State == Sent : ", req.state)						
						socket.sendto(('R|2|'+req.request_id+'|'+req.stream_id).encode(), (req.element,9090))
						request_dict.pop(req.request_id,req.element)
					elif req.state == "Active Retransmission":
						socket.sendto(('R|S|'+req.stream_id+'|'+str(stream_content[0])).encode(), (req.element,9090))
			

			return 0


