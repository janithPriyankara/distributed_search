# UDP server logic
import socket

def start_udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 9000))
    print('UDP server started on port 9000')
    while True:
        data, addr = sock.recvfrom(1024)
        print(f'Received from {addr}: {data}')
