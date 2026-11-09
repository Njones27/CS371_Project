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

#create the server socket, then bind and listen
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("127.0.0.1", 19999))
server.listen(5)



