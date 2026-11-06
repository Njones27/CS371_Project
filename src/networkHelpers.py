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


# Leftover bytes for each socket, kept between receiveMessage calls
buffers = {}

def sendMessage(sock: socket.socket, data: dict) -> None:
    # Package data into JSON text using \n to mark end of message
    packet = json.dumps(data) + "\n"
    # Convert text to bytes
    packet = packet.encode()
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
    # Turn the message from bytes back into a dict and return it
    return json.loads(message.decode())


