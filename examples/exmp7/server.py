import socket

# Create UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind server to IP and port
server_socket.bind(("127.0.0.1", 11111))

print("UDP server is ready...")

while True:
    # Receive data and the client's address
    data, addr = server_socket.recvfrom(1024)

    message = data.decode()
    print("Received:", message, "from", addr)

    # Convert message to uppercase
    reply = message.upper()

    # Send reply back to that client
    server_socket.sendto(reply.encode(), addr)