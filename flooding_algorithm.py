from class_objects import Request

def request_r(socket, request, origin_address, request_dict, neighbours_list):
    """
    This is a Python function that handles different types of requests and messages in a network
    communication system.
    
    :param socket: The socket object used for communication
    :param request: The request message received by the function, split into a list of strings
    :param origin_address: The IP address and port number of the element that sent the request to the
    current element
    :param request_dict: A dictionary containing information about all the requests made by different
    elements in the network. The keys of the dictionary are tuples of (request_id, element) and the
    values are objects of the Request class
    :param neighbours_list: A list of IP addresses of neighbouring nodes in the network
    :return: either 0, a tuple containing "stream" and a stream ID, or a tuple containing "cancel" and a
    stream ID.
    """
    type_of_message = request[1]

    if type_of_message == '0':
        req_ID = request[2]
        stream_ID = request[3]

        requests_with_id = [x for (k1, _), x in request_dict.items() if k1 == req_ID]
        if len(requests_with_id) > 0:
            if any(x.element == origin_address for x in requests_with_id):
                print("There's an existing request from this IP:")
            else:
                print("There isn't any request from that element")
                socket.sendto(('R|2|' + req_ID + '|' + stream_ID).encode(), origin_address)
        else:
            if any(str(x.stream_id) == str(stream_ID) and x.state == "Active Retransmission" for x in request_dict.values()):
                for req in request_dict.values():
                    if req.state == "Active Retransmission" and str(req.stream_id) == str(stream_ID):
                        print("Sent Confirmation for stream -> ", req.stream_id)
                        socket.sendto(('R|1|' + req_ID).encode(), origin_address)
                        rq_obj = Request(req_ID, stream_ID, "Answered", origin_address[0])
            else:
                if len(request) > 4:
                    rq_obj = Request(req_ID, stream_ID, "Received", origin_address[0], request[4])
                else:
                    rq_obj = Request(req_ID, stream_ID, "Received", origin_address[0])
                    print("ADDED Request:", rq_obj.__dict__.values())
                for neighbour in [x for x in neighbours_list if x != origin_address[0]]:
                    message = '|'.join(request)
                    socket.sendto(message.encode(), (neighbour, 9090))
                    rq_obj1 = Request(req_ID, stream_ID, "Sent", neighbour)
                    print("New requests sent:", rq_obj1.__dict__.values())
                    request_dict[req_ID, neighbour] = rq_obj1
            request_dict[req_ID, origin_address[0]] = rq_obj

        return 0

    elif type_of_message == '1':
        req_ID = request[2]
        requests_with_id = [x for (k1, _), x in request_dict.items() if k1 == req_ID]
        for x in requests_with_id:
            pass
        if any(x.element == origin_address[0] for x in requests_with_id):
            rq_obj = request_dict.get((req_ID, origin_address[0]))
            print(rq_obj)
            if rq_obj.state == "Sent":
                socket.sendto(('R|1|' + req_ID).encode(), origin_address)
                print("Sent a Confirmation to:", origin_address[0], "\nThis was the message:", 'R|1|' + req_ID)
                rq_obj.change_state("C")
            elif rq_obj.state == "Answered":
                rq_obj.change_state("AR")
                return ("stream", rq_obj.stream_id)
        elif any(x.element == socket.getsockname()[0] for x in requests_with_id):
            rq_obj = request_dict.get((req_ID, socket.getsockname()[0]))
            print(rq_obj)
            if rq_obj.state == "Sent":
                socket.sendto(('R|1|' + req_ID).encode(), origin_address)
                print("Sent a Confirmation to:", origin_address[0], "\nThis was the message:", 'R|1|' + req_ID)
                rq_obj.change_state("C")

    elif type_of_message == '2':
        req_ID = request[2]
        stream_ID = request[3]
        real_request = []

        requests_with_id = [x for (k1, _), x in request_dict.items() if k1 == req_ID]
        for request in request_dict.values():
            pass
        for req in requests_with_id:
            if req.state == "Sent" or req.state == "Active Retransmission" or req.state == "Confirmed":
                if req.element != origin_address[0]:
                    socket.sendto(('R|2|' + req_ID + '|' + stream_ID).encode(), (req.element, 9090))
            ret = request_dict.pop((req.request_id, req.element))
        for requ in request_dict.values():
            if len(requ.request_id) == 8:
                real_request.append(requ)
        if not any(x.stream_id == stream_ID for x in real_request):
            return ("cancel", stream_ID)
        return 0

    elif type_of_message == 'S':
        stream_ID = request[2]
        stream_content = request[3:]
        print("This is the stream content:", stream_content[0])
        print("Streaming TIME:", request[2])
        for req in request_dict.values():
            print("LIST OF REQUESTS entry:", req.request_id, "|", req.stream_id, "|", req.state, "|", req.element)
            if req.stream_id == stream_ID:
                if req.state == "Received":
                    print("req_state == received:", req.state)
                    socket.sendto(('R|1|' + req.request_id).encode(), (req.element, 9090))
                    req.change_state("A")
                elif req.state == "Sent":
                    print("Request State == Sent:", req.state)
                    socket.sendto(('R|2|' + req.request_id + '|' + req.stream_id).encode(), (req.element, 9090))
                    request_dict.pop(req.request_id, req.element)
                elif req.state == "Active Retransmission":
                    socket.sendto(('R|S|' + req.stream_id + '|' + str(stream_content[0])).encode(), (req.element, 9090))

        return 0