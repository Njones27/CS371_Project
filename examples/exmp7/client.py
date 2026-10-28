import socket

# Create UDP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server = ("127.0.0.1", 11111)

message = input("Enter a message: ")

while message.lower().strip() != "bye":

    # Send message directly to server
    client_socket.sendto(message.encode(), server)

    # Receive server's reply
    data, addr = client_socket.recvfrom(1024)

    print("From server:", data.decode())

    message = input("Enter a message: ")

client_socket.close()