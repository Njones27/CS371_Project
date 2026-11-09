# =================================================================================================
# Contributing Authors:	    Lucas Anderson
# Email Addresses:          lfan224@uky.edu
# Date:                     11-4-26
# Purpose:                  <How this file contributes to the project>
# Misc:                     <Not Required.  Anything else you might want to include>
# =================================================================================================

# sendMessage(socket.socket,data: dict)
# receiveMessage(socket.socket) -> dict
from networkHelpers import sendMessage, receiveMessage
import socket
import threading

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games

# Shared game state. Both client threads use these, so only touch them while holding stateLock
# Most recent update sent by each player, None until that player has sent one
gameState = {"left": None, "right": None}
# Lets only one thread at a time use the shared state above
stateLock = threading.Lock()


def handleClient(conn: socket.socket, side: str) -> None:
    # Purpose:      Runs in its own thread for one client. Every frame it receives that client's
    #               update, saves it, and sends back the other player's latest update
    # Arguments:
    # conn          The socket for this one client, returned by server.accept()
    # side          "left" or "right", the paddle this client controls

    # The other player's key in gameState
    opponentSide = "right" if side == "left" else "left"

    while True:
        # Wait for this client's next update. receiveMessage returns one full dictionary
        update = receiveMessage(conn)

        with stateLock:
            # Save this player's newest information for the other thread to read
            gameState[side] = update

            # Grab a copy of the opponent's latest update while still holding the lock. If the
            # opponent has not sent anything yet, answer with a waiting message instead
            opponentUpdate = gameState[opponentSide]
            reply = dict(opponentUpdate) if opponentUpdate is not None else {"waiting": True}

        # Send after the lock is released so a slow client never holds up the other player.
        # Every update gets exactly one reply, so the client can send then receive each frame
        sendMessage(conn, reply)


#create the server socket, then bind and listen
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 19999))
server.listen(5)

# Accept exactly two clients. The first to connect is the left paddle and the second is the right
clients = []
for side in ["left", "right"]:
    # Waits until a client connects, then gives back a socket just for that client
    conn, addr = server.accept()
    print(f"The {side} player connected from {addr[0]}")

    # Remember this client until both players have joined
    clients.append((conn, side))

# Both players have joined, so start the game for both of them at the same time
threads = []
for conn, side in clients:
    # One thread per client so the server can listen to both players at once
    t = threading.Thread(target=handleClient, args=(conn, side), daemon=True)
    t.start()
    threads.append(t)

# Keep the main program open until both client threads have finished
for t in threads:
    t.join()
