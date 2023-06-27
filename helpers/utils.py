import socket

host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP:', host_ip)
port = 9090
socket_address = (host_ip, port)
print("LISTENING AT:", socket_address)
off_flag = 0
BUFF_SIZE = 65536
