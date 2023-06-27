import socket
import time
import threading
import select

import helpers.flooding_algorithm as flood
from helpers.utils import BUFF_SIZE, off_flag, port, socket_address


class NetworkElement:
    def __init__(self):
        self.element_socket = None
        self.Active_neighbours = []
        self.Request_dict = dict()
        self.service_controller_ip = '10.0.1.10'

    def introduction_server(self, socket):
        hello_msg = 'C|0|'
        try:
            socket.sendto(hello_msg.encode(), (self.service_controller_ip, port))
        except Exception as e:
            raise e

    def add_active_neighbour(self, neighbour):
        if neighbour not in self.Active_neighbours:
            self.Active_neighbours.append(neighbour)
        else:
            print("Neighbour already active")

    def handle_requests(self, socket):
        global off_flag

        while off_flag == 0:
            r, _, _ = select.select([socket], [], [], 0)
            if r:
                (rq, peer_address) = socket.recvfrom(BUFF_SIZE)
                request = rq.decode().split('|')

                match request[0]:
                    case 'C':
                        if request[1] == '0':
                            if len(request) > 2:
                                neighbour_list = request[2].split(';')
                                for neighbour in neighbour_list:
                                    self.add_active_neighbour(neighbour)
                            else:
                                time.sleep(3)
                                self.introduction_server(socket)
                    case 'R':
                        out = flood.request_r(socket, request, peer_address, self.Request_dict, self.Active_neighbours)

    def run_network_element(self):
        self.element_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.element_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
        self.element_socket.bind(socket_address)

        self.introduction_server(self.element_socket)
        receiver_thread = threading.Thread(target=self.handle_requests, args=(self.element_socket,))
        receiver_thread.start()
        leave = input("Press 'x' to leave\n")
        if leave == "x":
            for ip in self.Active_neighbours:
                requests_with_IP = [x for (_, k2), x in self.Request_dict.items() if k2 == ip]
                for req in requests_with_IP:
                    self.element_socket.sendto(('R|2|' + req.request_id + '|' + req.stream_id).encode(), (ip, port))

            off_flag = 1

        receiver_thread.join()
