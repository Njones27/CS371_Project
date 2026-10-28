import socket, threading

clients = {}  # list of connected clients
count = 1

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")
    client_number = clients[conn]
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:  # client disconnected
                break
            # broadcast message to everyone except the sender
            
            
            msg = f'\nClient {client_number}: ' + msg.decode()
            msg = msg.encode()
            for c in clients:
                if c != conn:
                    c.send(msg)
        except:
            break
    # cleanup after disconnect
    conn.close()
    if conn in clients:
        clients.pop(conn)
    print(f"[DISCONNECTED] {addr}")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind(("0.0.0.0", 65432))   # listen on all interfaces, port 65432
server.listen()

print("Server listening on port 65432...")

while True:
    conn, addr = server.accept()
    clients[conn] = count
    count += 1
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()
