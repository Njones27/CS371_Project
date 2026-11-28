# =================================================================================================
# Contributing Authors:	    Lucas Anderson, Nathan Jones, Ryan Rice
# Email Addresses:          lfan224@uky.edu, njjo227@uky.edu, rlri231@uky.edu
# Date:                     11.28.2026
# Purpose:                  The server side of the game. It accepts two players (and any number of
#                           spectators after them), checks each client's login, and every frame passes
#                           each player's paddle, ball, score and sync to the other player. It also saves
#                           wins to leaderboard.json and shows them on a webpage on port 80
# Misc:                     Every message goes through networkHelpers.py, so it is encrypted. Run with
#                           sudo on Mac or Linux so the leaderboard can use port 80, otherwise it uses 8080
# =================================================================================================

# sendMessage(socket.socket,data: dict)
# receiveMessage(socket.socket) -> dict
from networkHelpers import sendMessage, receiveMessage
import socket
import threading
import json
import os
import html
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

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

# File the player accounts are saved in. It only holds a salted hash of each password, never the password
ACCOUNTS_FILE = "accounts.json"
# How many times the password is hashed. More rounds make guessing passwords from the file much slower
HASH_ROUNDS = 100_000
# Lets only one thread at a time read or write the accounts file (players and spectators can join at once)
accountsLock = threading.Lock()

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
# Each player's socket, so when one player leaves their thread can also hang up on the other player
connections = {"left": None, "right": None}


def loadWins() -> dict:
    # Author:       Nathan Jones
    # Purpose:      Reads the saved win counts from the leaderboard file
    # Pre:          The server was started from the folder leaderboard.json is kept in. The file may
    #               not exist yet if nobody has won a game
    # Post:         Returns a dictionary of initials to wins, for example {"NJ": 3, "RR": 2}, or {} if
    #               there is no file yet. Nothing is changed

    # No file yet means nobody has won a game
    if not os.path.exists(LEADERBOARD_FILE):
        return {}
    with open(LEADERBOARD_FILE, "r") as f:
        return json.load(f)

def synchronizeGames(update: dict, opponentUpdate: dict) -> dict:
    # Author:       Lucas Anderson (Ryan Rice fixed the reply so paddleY and sync are kept)
    # Purpose:      Compares the two players' game states and builds the reply for this player
    # Pre:          update is this client's newest update. opponentUpdate is the opponent's newest
    #               update, or None if the opponent has not sent one yet. Called while holding stateLock
    # Post:         Returns {"waiting": True} if the opponent has not sent anything yet, otherwise a copy
    #               of the opponent's update, plus "syncDifference" if the games are more than 2 frames
    #               apart. Neither update is changed

    if opponentUpdate is None:
        return {"waiting": True}
    #compare clients to see if they are far enough apart to warrant a syncing
    syncDifference = abs(update.get("sync", 0) - opponentUpdate.get("sync", 0))
    # Always send the opponent's full update. The client looks for "paddleY" and compares
    # reply["sync"] (a frame number) with its own to copy the ahead player's ball and score,
    # so those keys have to stay at the top level and "sync" must not be replaced with True
    reply = dict(opponentUpdate)
    #if they are far apart, also say by how much
    if syncDifference > 2:
        reply["syncDifference"] = syncDifference
    return reply


def recordWin(playerInitials: str) -> None:
    # Author:       Nathan Jones
    # Purpose:      Adds one win for a player and saves the leaderboard file
    # Pre:          playerInitials are the initials the winning player typed in. Called while holding
    #               stateLock so two threads never write the file at once
    # Post:         leaderboard.json holds one more win for playerInitials (starting from 0 for a new
    #               player)

    wins = loadWins()
    # A player who has never won before starts at 0
    wins[playerInitials] = wins.get(playerInitials, 0) + 1
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(wins, f)


def findWinner(update: dict, opponentUpdate: dict) -> str:
    # Author:       Nathan Jones
    # Purpose:      Works out if the game is over, using the same "more than 4" rule as the win
    #               message in pongClient.py. Both players' games have to agree before it counts,
    #               because the two games can be a frame or two apart
    # Pre:          update is the newest update from one player. opponentUpdate is the newest update
    #               from the other player, or None if there is not one yet
    # Post:         Returns "left" or "right" for the winning side, or "" if nobody has won yet.
    #               Nothing is changed

    if opponentUpdate is None:
        return ""
    if update.get("lScore", 0) > 4 and opponentUpdate.get("lScore", 0) > 4:
        return "left"
    if update.get("rScore", 0) > 4 and opponentUpdate.get("rScore", 0) > 4:
        return "right"
    return ""


def handleClient(conn: socket.socket, side: str) -> None:
    # Author:       Nathan Jones (game loop and Play Again). Ryan Rice (disconnect handling)
    # Purpose:      Runs in its own thread for one client. Every frame it receives that client's
    #               update, saves it, and sends back the other player's latest update
    # Pre:          conn is a player that joined through readHello and was sent the setup message.
    #               side is "left" or "right", the paddle this client controls
    # Post:         Ends when either player disconnects. conn is closed and the other player's socket
    #               is shut down so their game closes too
    global winRecorded

    # The other player's key in gameState
    opponentSide = "right" if side == "left" else "left"

    try:
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
                        reply = synchronizeGames(update, opponentUpdate)

            # Send after the lock is released so a slow client never holds up the other player.
            # Every update gets exactly one reply, so the client can send then receive each frame
            sendMessage(conn, reply)

    # The player closed their game or lost their connection. ConnectionError comes from receiveMessage
    # when the client hangs up, OSError covers other network errors and ValueError a half sent message
    except (ConnectionError, OSError, ValueError) as e:
        print(f"The {side} player disconnected: {e}")

    # finally runs no matter how the loop ended, so the sockets always get cleaned up
    finally:
        conn.close()
        # Hang up on the other player too, so their game closes instead of playing against a frozen
        # paddle. shutdown() wakes up their thread, which is stuck waiting in receiveMessage, and
        # their client sees the connection close and exits through quitGame
        otherConn = connections[opponentSide]
        if otherConn is not None:
            try:
                otherConn.shutdown(socket.SHUT_RDWR)
            except OSError:
                # Already closed, because that player left first
                pass


def hashPassword(password: str, salt: str) -> str:
    # Author:       Ryan Rice
    # Purpose:      Turns a password into a hash that can be stored safely. The same password and salt
    #               always give the same hash, but the hash cannot be turned back into the password
    # Pre:          salt is a random hex string saved with the account when it was registered
    # Post:         Returns the hash as a hex string. Nothing is changed

    # pbkdf2_hmac runs sha256 HASH_ROUNDS times. The salt makes two players with the same password
    # end up with different hashes
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), HASH_ROUNDS).hex()


def checkLogin(username: str, password: str) -> str:
    # Author:       Ryan Rice
    # Purpose:      Registration and authentication. A username that is not in accounts.json is
    #               registered with this password. A username that is already there has to match its
    #               saved password
    # Pre:          username and password are not empty
    # Post:         Returns "" if the player may join, or a message saying why not. A new account is
    #               saved to accounts.json

    with accountsLock:
        accounts = {}
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, "r") as f:
                accounts = json.load(f)

        # Registration: a new username gets a random salt and the hash of its password
        if username not in accounts:
            salt = os.urandom(16).hex()
            accounts[username] = {"salt": salt, "hash": hashPassword(password, salt)}
            with open(ACCOUNTS_FILE, "w") as f:
                json.dump(accounts, f)
            print(f"Registered a new account: {username}")
            return ""

        # Authentication: hash the password the same way and compare it with the saved hash.
        # compare_digest takes the same time whether the hashes match early or late, so the timing
        # does not give away how much of a guess was right
        saved = accounts[username]
        if hmac.compare_digest(hashPassword(password, saved["salt"]), saved["hash"]):
            return ""
        return f"Wrong password for {username}"


def readHello(conn: socket.socket, addr: tuple) -> Optional[dict]:
    # Author:       Ryan Rice
    # Purpose:      Reads the first message from a new client, which every client sends right after
    #               connecting. Players and spectators both go through here, so any check on who may
    #               join (the wrong key now, and the login later) only has to be written once
    # Pre:          conn was just returned by server.accept() and nothing has been read from it yet
    # Post:         Returns the client's first message as a dictionary. If the client could not join
    #               (wrong secret.key, missing initials or login, wrong password, or it hung up) it is
    #               sent the reason when possible, conn is closed and None is returned

    try:
        hello = receiveMessage(conn)
        # Every client has to send initials, a username and a password
        if not hello.get("initials"):
            raise ValueError("no initials were sent")
        username = str(hello.get("username", "")).strip()
        password = str(hello.get("password", ""))
        if not username or not password:
            raise ValueError("no username or password was sent")

        # Registration and authentication
        error = checkLogin(username, password)
        if error:
            print(f"Turned away a client from {addr[0]}: {error}")
            # Tell the client why so it can show the message on the start screen
            sendMessage(conn, {"error": error})
            conn.close()
            return None
        return hello
    # ValueError means the message could not be decrypted (wrong key), was not valid JSON or was
    # missing something. The client may not even have our key, so nothing is sent back
    except (ConnectionError, OSError, ValueError) as e:
        print(f"Turned away a client from {addr[0]}, it could not join: {e}")
        conn.close()
        return None


def handleSpectator(conn: socket.socket, number: int) -> None:
    # Author:       Ryan Rice
    # Purpose:      Runs in its own thread for one spectator. Every frame the spectator asks for the
    #               game and gets back both players' latest updates, so it can draw both paddles, the
    #               ball and the score. A spectator only reads gameState, it never changes the game
    # Pre:          conn has joined through readHello and was sent the setup message with
    #               "playerPaddle": "spectator"
    # Post:         Ends when the spectator leaves or the server closes. conn is closed and the game
    #               is not affected

    try:
        while True:
            # The spectator sends {"spectator": True} every frame. Its content is not needed, it keeps
            # the same send then receive rhythm the players use, so one reply goes back per message
            receiveMessage(conn)
            # Copy both players' newest updates while holding the lock, the same way handleClient does
            with stateLock:
                reply = {"left": gameState["left"], "right": gameState["right"]}
            sendMessage(conn, reply)
    except (ConnectionError, OSError, ValueError) as e:
        print(f"Spectator {number} left: {e}")
    finally:
        conn.close()


def acceptSpectators() -> None:
    # Author:       Ryan Rice
    # Purpose:      Keeps accepting new clients after both players have joined. Every extra client
    #               becomes a spectator with its own thread, so any number of clients can be connected
    # Pre:          Both players have joined and their game threads are running
    # Post:         Runs until the server exits. Each spectator that joins is sent the screen size with
    #               "playerPaddle": "spectator" and gets a handleSpectator thread

    number = 0
    while True:
        conn, addr = server.accept()
        hello = readHello(conn, addr)
        # readHello already closed a client that could not join, so just wait for the next one
        if hello is None:
            continue
        number += 1
        print(f"Spectator {number} ({hello['initials']}) connected from {addr[0]}")
        try:
            # Same setup message the players get. "spectator" tells the client not to control a paddle
            sendMessage(conn, {"screenWidth": SCREEN_WIDTH, "screenHeight": SCREEN_HEIGHT,
                               "playerPaddle": "spectator"})
        except OSError:
            conn.close()
            continue
        # daemon=True so spectators never keep the server open after the game is over
        threading.Thread(target=handleSpectator, args=(conn, number), daemon=True).start()


class LeaderboardHandler(BaseHTTPRequestHandler):
    # Author:       Nathan Jones
    # Purpose:      Answers web browser requests with the leaderboard page

    def do_GET(self) -> None:
        # Author:       Nathan Jones
        # Purpose:      Runs every time a browser asks for a page. Any path shows the leaderboard
        # Pre:          A browser connected to the leaderboard port. The request details are stored on
        #               self by BaseHTTPRequestHandler
        # Post:         The browser was sent a page listing every player's wins, most wins first

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
    # Author:       Nathan Jones
    # Purpose:      Starts the leaderboard webpage in its own thread so it runs next to the game
    # Pre:          Called once, before any players join
    # Post:         The page is running on port 80, or 8080 if 80 could not be opened, and the port is
    #               printed. If neither port works it prints that the page is off and the game still runs

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
    # Keep accepting until a client joins properly. A client with the wrong secret.key (or one that
    # hangs up right away) is turned away, and the server waits for someone else to take this side
    while True:
        # Waits until a client connects, then gives back a socket just for that client
        conn, addr = server.accept()
        # The first message from the client holds its initials for the leaderboard
        hello = readHello(conn, addr)
        if hello is not None:
            break
    print(f"The {side} player connected from {addr[0]}")
    initials[side] = hello["initials"]

    # Remember this client until both players have joined
    clients.append((conn, side))
    connections[side] = conn

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

# The game has started, so every client that connects from now on is a spectator
threading.Thread(target=acceptSpectators, daemon=True).start()

# Keep the main program open until both client threads have finished
for t in threads:
    t.join()
