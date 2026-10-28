import socket
import threading

def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(1024).decode()
            if not msg:
                break
            print(f"\r\033[K{msg}\n-> ", end="")
        except:
            break

def client_program():
    host = "127.0.0.1"  # change to server IP if needed
    port = 65432

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    # start thread for receiving messages
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    # main loop for sending messages
    while True:
        msg = input("->")
        if msg.lower().strip() == "bye":
            sock.send(msg.encode())
            sock.close()
            break
        sock.send(msg.encode())

if __name__ == "__main__":
    client_program()
