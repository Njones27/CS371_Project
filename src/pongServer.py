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
import json
import os
import html
from http.server import BaseHTTPRequestHandler, HTTPServer

# Use this file to write your server logic
# You will need to support at least two clients
# You will need to keep track of where on the screen (x,y coordinates) each paddle is, the score 
# for each player and where the ball is, and relay that to each client
# I suggest you use the sync variable in pongClient.py to determine how out of sync your two
# clients are and take actions to resync the games

# Screen size sent to both clients so the two games always match
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# File the win counts are saved in, so they are still there after the server restarts
LEADERBOARD_FILE = "leaderboard.json"

# Port for the leaderboard webpage, plus a backup for when the server is not run as admin
WEB_PORT = 80
BACKUP_WEB_PORT = 8080

# Shared game state. Both client threads use these, so only touch them while holding stateLock
# Most recent update sent by each player, None until that player has sent one
gameState = {"left": None, "right": None}
# Initials each player typed in, used as their name on the leaderboard
initials = {"left": "", "right": ""}
# True once the current game's win has been saved, so a game is only counted one time
winRecorded = False
# Sides that have pressed space to play again
playAgainVotes = set()
# Sides that still need to be told the game was reset
resetPending = set()
# Lets only one thread at a time use the shared state above
stateLock = threading.Lock()


def loadWins() -> dict:
    # Purpose:      Reads the saved win counts from the leaderboard file
    # Returns:      A dictionary of initials to wins, for example {"NJ": 3, "RR": 2}

    # No file yet means nobody has won a game
    if not os.path.exists(LEADERBOARD_FILE):
        return {}
    with open(LEADERBOARD_FILE, "r") as f:
        return json.load(f)


def recordWin(playerInitials: str) -> None:
    # Purpose:      Adds one win for a player and saves the leaderboard file
    # Arguments:
    # playerInitials    The initials of the player who won the game

    wins = loadWins()
    # A player who has never won before starts at 0
    wins[playerInitials] = wins.get(playerInitials, 0) + 1
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(wins, f)


def findWinner(update: dict, opponentUpdate: dict) -> str:
    # Purpose:      Works out if the game is over, using the same "more than 4" rule as the win
    #               message in pongClient.py. Both players' games have to agree before it counts,
    #               because the two games can be a frame or two apart
    # Arguments:
    # update            The newest update from one player
    # opponentUpdate    The newest update from the other player, or None if there is not one yet
    # Returns:      "left" or "right" for the winning side, or "" if nobody has won yet

    if opponentUpdate is None:
        return ""
    if update.get("lScore", 0) > 4 and opponentUpdate.get("lScore", 0) > 4:
        return "left"
    if update.get("rScore", 0) > 4 and opponentUpdate.get("rScore", 0) > 4:
        return "right"
    return ""


def handleClient(conn: socket.socket, side: str) -> None:
    # Purpose:      Runs in its own thread for one client. Every frame it receives that client's
    #               update, saves it, and sends back the other player's latest update
    # Arguments:
    # conn          The socket for this one client, returned by server.accept()
    # side          "left" or "right", the paddle this client controls
    global winRecorded

    # The other player's key in gameState
    opponentSide = "right" if side == "left" else "left"

    while True:
        # Wait for this client's next update. receiveMessage returns one full dictionary
        update = receiveMessage(conn)

        with stateLock:
            if side in resetPending:
                # This client has not heard about the rematch yet. Its update still holds the old
                # winning score, so throw it away and tell the client to reset
                resetPending.discard(side)
                reply = {"reset": True}
            else:
                # Save this player's newest information for the other thread to read
                gameState[side] = update

                # Count the win one time. findWinner only names a winner once both games agree
                winnerSide = findWinner(update, gameState[opponentSide])
                if not winRecorded and winnerSide:
                    recordWin(initials[winnerSide])
                    winRecorded = True

                # Remember that this player asked for a rematch
                if update.get("playAgain"):
                    playAgainVotes.add(side)

                if playAgainVotes == {"left", "right"}:
                    # Both players want a rematch, so wipe the old game
                    playAgainVotes.clear()
                    gameState["left"] = None
                    gameState["right"] = None
                    winRecorded = False
                    # This client is told right now, the other one on its next update
                    resetPending.add(opponentSide)
                    reply = {"reset": True}
                else:
                    # Normal frame. Grab a copy of the opponent's latest update while still holding
                    # the lock. If the opponent has not sent anything yet, answer with a waiting message
                    opponentUpdate = gameState[opponentSide]
                    reply = dict(opponentUpdate) if opponentUpdate is not None else {"waiting": True}

        # Send after the lock is released so a slow client never holds up the other player.
        # Every update gets exactly one reply, so the client can send then receive each frame
        sendMessage(conn, reply)


class LeaderboardHandler(BaseHTTPRequestHandler):
    # Purpose:      Answers web browser requests with the leaderboard page

    def do_GET(self) -> None:
        # Purpose:      Runs every time a browser asks for a page. Any path shows the leaderboard

        # Read the saved wins inside the lock so a game thread is never writing the file at the same time
        with stateLock:
            wins = loadWins()
        # Most wins first
        ranked = sorted(wins.items(), key=lambda item: item[1], reverse=True)

        # One table row per player. html.escape makes odd initials show up as plain text
        rows = "".join(f"<tr><td>{html.escape(name)}</td><td>{count}</td></tr>" for name, count in ranked)
        body = ("<html><head><title>Pong Leaderboard</title></head><body><h1>Pong Leaderboard</h1>"
                f"<table><tr><th>Player</th><th>Wins</th></tr>{rows}</table></body></html>").encode()

        # 200 means OK. The headers tell the browser it is a webpage and how many bytes long it is
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def startLeaderboard() -> None:
    # Purpose:      Starts the leaderboard webpage in its own thread so it runs next to the game

    # Port 80 needs admin rights, so try the backup port if it cannot be opened
    for port in [WEB_PORT, BACKUP_WEB_PORT]:
        try:
            webServer = HTTPServer(("0.0.0.0", port), LeaderboardHandler)
        except OSError as e:
            print(f"Could not start the leaderboard on port {port}: {e}")
            continue
        # daemon=True so this thread never keeps the server open by itself
        threading.Thread(target=webServer.serve_forever, daemon=True).start()
        print(f"Leaderboard running on port {port}")
        return
    print("The leaderboard page is off for this run, the game itself still works")


#create the server socket, then bind and listen
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Lets the server be restarted right away without an "address already in use" error
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 0.0.0.0 accepts connections from other computers, 127.0.0.1 only accepted this one
server.bind(("0.0.0.0", 19999))
server.listen(5)

# Start the leaderboard webpage before any players join
startLeaderboard()

# Accept exactly two clients. The first to connect is the left paddle and the second is the right
clients = []
for side in ["left", "right"]:
    # Waits until a client connects, then gives back a socket just for that client
    conn, addr = server.accept()
    print(f"The {side} player connected from {addr[0]}")

    # The first message from the client is its initials for the leaderboard
    hello = receiveMessage(conn)
    initials[side] = hello["initials"]

    # Remember this client until both players have joined
    clients.append((conn, side))

# Both players have joined, so start the game for both of them at the same time
threads = []
for conn, side in clients:
    # Tell the client the screen size and which paddle it controls. The client waits for this
    # message before it opens the game window
    sendMessage(conn, {"screenWidth": SCREEN_WIDTH, "screenHeight": SCREEN_HEIGHT, "playerPaddle": side})

    # One thread per client so the server can listen to both players at once
    t = threading.Thread(target=handleClient, args=(conn, side), daemon=True)
    t.start()
    threads.append(t)

# Keep the main program open until both client threads have finished
for t in threads:
    t.join()
