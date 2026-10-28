import socket

HOST = "127.0.0.1"  # server address
PORT = 5000         # must match server port

def client_program():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    print("Connected to server. Type messages (type 'bye' to quit).")

    while True:
        msg = input("You -> ")
        if msg.lower().strip() == "bye":
            break
        client_socket.send(msg.encode())
        data = client_socket.recv(1024).decode()
        print("Server ->", data)

    client_socket.close()

if __name__ == "__main__":
    client_program()
