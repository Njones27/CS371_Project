import socket, select

HOST = "127.0.0.1"
PORT = 5000

# create TCP server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

# list of sockets to monitor for reading
inputs = [server_socket]

print(f"Server listening on {HOST}:{PORT}")

while True:
    readable, _, _ = select.select(inputs, [], [], 1)
    for s in readable:
        if s is server_socket:
            # new client
            conn, addr = server_socket.accept()
            print(f"[NEW CONNECTION] {addr}")
            inputs.append(conn)
        else:
            # message from existing client
            data = s.recv(1024)
            if not data:
                print("[DISCONNECTED]")
                inputs.remove(s)
                s.close()
            else:
                print("Received:", data.decode())
                s.send(b"Echo: " + data)
