import socket

client = socket.socket()
client.connect(("127.0.0.1", 65432))

while True:
    cmd = input("Enter command (or 'exit'): ")
    if cmd.lower() == "exit":
        client.send(b"exit")
        break
    client.send(cmd.encode())
    output = client.recv(4096).decode()
    print(output)

client.close()

