import socket
import time
import threading
from helpers.class_objects import Stream, Request

def request_r(socket, request, origin_address, request_dict, neighbours_list):
	type_of_message = request[1]

	match type_of_message:
		# This code block is handling the request message with type '0'. It first extracts the request ID
		# and stream ID from the message. Then, it checks if there are any existing requests with the same
		# request ID. If there are, it checks if any of them were sent from the same IP address as the
		# current request. If there is a match, it prints a message indicating that there is already a
		# request from that IP address. Otherwise, it sends a message of type '2' to the origin address
		# indicating that there are no requests from that IP address. If there are no existing requests with
		# the same request ID, it checks if there is an active retransmission for the desired stream ID. If
		# there is, it sends a message of type '1' to the origin address indicating that the request has
		# been answered. If there is no active retransmission, it adds the request to the request dictionary
		# and sends the request to all neighbors except the origin address. Finally, it adds the request to
		# the request dictionary with the origin address as the element and returns 0.
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
			
		# This code block is handling the request message with type '1'. It first extracts the request ID
		# from the message and checks if there are any existing requests with the same request ID. If there
		# are, it checks if any of them were sent from the same IP address as the current request. If there
		# is a match, it sends a message of type '1' to the origin address indicating that the request has
		# been answered. If there is no match, it returns the stream ID so it may be transmitted on the
		# node.
		case '1':
			req_ID = request[2]
			requests_with_id = [x for (k1,_), x in request_dict.items() if k1 == req_ID]
			for x in requests_with_id:
				pass
			if any(x.element == origin_address[0] for x in requests_with_id):
				rq_obj = request_dict.get((req_ID, origin_address[0]))
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
				if rq_obj.state == "Sent":
					socket.sendto(('R|1|'+req_ID).encode(), origin_address)
					print("Sent a Confirmation to: ", origin_address[0], "\nThis was the message: ", 'R|1|'+req_ID)
					rq_obj.change_state("C")

		# This code block is handling the request message with type '2'. It first extracts the request ID
		# and stream ID from the message. Then, it checks if there are any existing requests with the same
		# request ID. If there are, it sends a message of type '2' to all nodes except the origin address
		# indicating that the request has been cancelled. It also removes the request from the request
		# dictionary. Finally, it checks if there are any remaining requests with the same stream ID. If
		# there are not, it returns a tuple with the string "cancel" and the stream ID so that the stream
		# may be cancelled on the node. If there are remaining requests with the same stream ID, it returns
		# 0.
		case '2':
			req_ID = request[2]
			stream_ID = request[3]
			real_request=[]

			requests_with_id = [x for (k1,_), x in request_dict.items() if k1 == req_ID]
			for request in request_dict.values():
				pass
			for req in requests_with_id:
				if req.state == "Sent" or req.state == "Active Retransmission" or req.state == "Confirmed":
					if req.element != origin_address[0]:
						socket.sendto(('R|2|'+req_ID+'|'+stream_ID).encode(), (req.element,9090))
				ret = request_dict.pop((req.request_id, req.element))
			for requ in request_dict.values():
				if len(requ.request_id)==8:
					real_request.append(requ)
			if not any(x.stream_id == stream_ID for x in real_request):
				return ("cancel", stream_ID)
			return 0
		
		# This code block is handling the request message with type 'S', which is used for streaming
		# content. It extracts the stream ID and stream content from the message and then iterates through
		# the request dictionary to find any requests that match the stream ID. For each matching request,
		# it checks the state of the request. If the state is "Received", it sends a message of type '1' to
		# the element indicating that the request has been answered and changes the state of the request to
		# "Answered". If the state is "Sent", it sends a message of type '2' to the element indicating that
		# the request has been cancelled and removes the request from the request dictionary. If the state
		# is "Active Retransmission", it sends a message of type 'S' to the element with the stream content.
		# Finally, it returns 0.
		case 'S':
			stream_ID = request[2]
			stream_content = request[3:]
			print("Stream content: ", stream_content[0])
			for req in request_dict.values():
				#print("LIST OF REQUESTS entry:", req.request_id,"|", req.stream_id,"|", req.state,"|" ,req.element)

				if req.stream_id == stream_ID :
		
					if req.state == "Received":
						socket.sendto(('R|1|'+req.request_id).encode(), (req.element,9090))
						req.change_state("A")
					elif req.state == "Sent":				
						socket.sendto(('R|2|'+req.request_id+'|'+req.stream_id).encode(), (req.element,9090))
						request_dict.pop(req.request_id,req.element)
					elif req.state == "Active Retransmission":
						socket.sendto(('R|S|'+req.stream_id+'|'+str(stream_content[0])).encode(), (req.element,9090))
			

			return 0


