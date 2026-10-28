import socket

# Create IPv4 TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


server_socket.bind(("127.0.0.1", 5000))  # bind to localhost:5000
server_socket.listen(1)                  # listen for 1 connection

print("Server waiting for a connection...")
conn, addr = server_socket.accept()      # accept a single client
print("Connected by", addr)

# Receive one message
data = conn.recv(1024)
print("Received:", data.decode())

# Send one reply
conn.send(b"Hello from server!")

conn.close()
server_socket.close()
