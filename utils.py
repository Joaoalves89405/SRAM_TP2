import socket

host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
port = 9090
socket_address = (host_ip, port)
off_flag = 0
BUFF_SIZE = 65536
