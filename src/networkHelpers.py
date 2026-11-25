# =================================================================================================
# Contributing Authors:	    Ryan Rice
# Email Addresses:          rlri231@uky.edu
# Date:                     11.06.2026
# Purpose:                  <Network helper functions that are shared between client and server
#                            this includes sending and receiving information>
# Misc:                     <Not Required.  Anything else you might want to include>
# =================================================================================================

import json
import socket
import os
from cryptography.fernet import Fernet, InvalidToken #used for encrypted communication:

# Leftover bytes for each socket, kept between receiveMessage calls
buffers = {}
KEY_FILE = os.path.join(os.path.dirname(__file__),"secret.key")
file = open(KEY_FILE, "rb")
try:
    key = file.read().strip()
finally:
    file.close()
cipher = Fernet(key)


def sendMessage(sock: socket.socket, data: dict) -> None:
    # Package data into JSON text using \n to mark end of message
    packet = json.dumps(data) #\n character that marks end of packet
    # must be added after encryption or it will be encrypted 
    # Convert text to bytes
    packet = packet.encode()
    # Encrypt packet
    packet = cipher.encrypt(packet)
    # since packet was converted to bytes using encode b"\n" must be used
    packet = packet + b"\n"
    # Send packet
    sock.sendall(packet)

# Receives one message and returns it as a dict
def receiveMessage(sock: socket.socket) -> dict:
    # Start with any bytes left over from the last call
    buffer = buffers.get(sock, b"")
    # Keep reading until a complete message has arrived
    while b"\n" not in buffer:
        chunk = sock.recv(1024)
        # Empty bytes means the other side closed the connection
        if chunk == b"":
            raise ConnectionError("Connection closed")
        buffer += chunk
    # Split off one complete message and keep the rest
    message, buffer = buffer.split(b"\n", 1)
    # Save the leftovers for the next call
    buffers[sock] = buffer
    # decrypt then turn the message from bytes back into a dict and return it
    try:
        message = cipher.decrypt(message)
    except InvalidToken:
        raise ValueError("Could not decrypt message")
    return json.loads(message.decode())


