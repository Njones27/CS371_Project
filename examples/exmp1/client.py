import socket

# Create IPv4 TCP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client_socket.connect(("127.0.0.1", 5000))   # connect to server

# Send one message
client_socket.send(b"Hello from client!")

# Receive one reply
data = client_socket.recv(1024)
print("Received:", data.decode())

client_socket.close()
