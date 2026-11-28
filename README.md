# CS371_Project
Repo for the CS371 Networking course project

Contact Info
============

Group Members & Email Addresses:

    Ryan Rice, rlri231@uky.edu
    Nathan Jones, njjo227@uky.edu
    Lucas Anderson, lfan224@uky.edu

Versioning
==========

Github Link: https://github.com/Njones27/CS371_Project

General Info
============
This is a two player Pong game that is played over the network. One computer runs the server and
each player runs the client. The server passes each player's paddle, ball and score information to
the other player so both screens show the same game. Every message between the client and the
server is encrypted, and every player logs in with a username and password.

Install Instructions
====================

The project needs Python 3 and the libraries in `requirements.txt` (pygame and cryptography).
Using a virtual environment keeps them separate from the rest of the computer, and on newer Linux
versions pip will not install into the system Python without one.

From the top folder of the project:

Mac or Linux:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Windows:

    py -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt

Run `source venv/bin/activate` (or `venv\Scripts\activate` on Windows) again in every new terminal
before starting the server or the client.

The client and the server both need the same `src/secret.key` file. It holds the encryption key,
so a copy of the project from this repo already works. If the key on one computer is different, that
client is turned away by the server.

Starting the server
===================

1. Open a terminal in the `src` folder and activate the virtual environment.
2. Run `python3 pongServer.py`.
   - The leaderboard webpage uses port 80, which needs admin rights on Mac and Linux. To get port
     80, run `sudo ../venv/bin/python pongServer.py` instead. Plain `sudo python3` uses the system
     Python, which does not have the libraries from the virtual environment.
   - Without admin rights the server prints a message and puts the leaderboard on port 8080. The
     game itself works either way.
3. Leave it running. The game uses port 19999.

Joining a game
==============

1. Open a terminal in the `src` folder and activate the virtual environment. The client has to be
   started from this folder because it loads its fonts, sounds and logo from `./assets`.
2. Run `python3 pongClient.py`.
3. Fill in the start screen and click Join:
   - Server IP: `127.0.0.1` if the server is on the same computer, otherwise the IP address of the
     computer running the server (run `ipconfig` on Windows or `ifconfig` on Mac and Linux to find it).
   - Server Port: `19999`
   - Initials: 1 to 3 letters or numbers, used for the leaderboard
   - Username and Password: see Registration and Login below
4. The first player to join is the left paddle and the second player is the right paddle. The
   first player's window says it is waiting for another player, and the game opens on both
   computers once the second player has joined.
5. Anyone who joins after the two players watches as a spectator.

Playing:

- The up and down arrow keys move your paddle.
- The first player to reach 5 points wins.
- Closing the window ends the game. If either player leaves, the other player's game closes too.

Playing on two computers:

- Both computers need to be able to reach each other, for example by both being on the UK VPN.
- The firewall on the server's computer has to allow incoming connections to Python.

Bonus Features
==============

Any Number of Clients (Spectators):

- After both players have joined, the server keeps accepting clients. Each one gets its own thread
  and joins as a spectator. There is no limit on how many can watch.
- A spectator's window says "Spectating" at the bottom and shows both paddles, the ball and the
  score as the game is played. The arrow keys do nothing for a spectator.
- Spectators log in the same way players do.

Play Again:

- When a player wins, both screens show the win message with "Space to play again" under it.
- Press space to ask for a rematch. The text changes to "Waiting for opponent" until the other
  player presses space too.
- Once both players have pressed space the score goes back to 0 to 0 and a new game starts. Each
  player keeps the same paddle.

Initials and Leaderboard:

- Each player types 1 to 3 letters or numbers in the Initials box before clicking Join. Lower case
  letters are changed to upper case, so "nj" and "NJ" are the same player.
- Every time a game ends the server adds one win for the winner's initials. The wins are saved in
  `leaderboard.json` in the folder the server was started from, so they are still there after the
  server is restarted.
- To see the leaderboard, open a web browser while the server is running and go to
  `http://<server ip>/`, or `http://127.0.0.1/` on the computer running the server. It lists every
  player's initials and wins with the most wins at the top. Refresh the page to see new wins.
- If the server could not open port 80 it prints a message and uses port 8080 for the leaderboard,
  so go to `http://<server ip>:8080/` in that case.

Registration and Login:

- The first time a username is used, the server registers it with the password that was typed in.
- After that, the same username only works with the same password. A wrong password shows
  "Wrong password for <username>" on the start screen and the player can try again.
- The server saves accounts in `accounts.json` in the folder it was started from. It never saves
  the password itself, only a salted hash of it (PBKDF2 with SHA-256 and 100,000 rounds), so the
  passwords cannot be read from the file. Delete `accounts.json` to remove every account.

Encryption:

- Every message between the client and the server is encrypted with Fernet (AES with an HMAC to
  catch changed messages) from the `cryptography` library, using the shared key in `src/secret.key`.
  This includes the username and password, so they are never sent as plain text.
- A client with a different key cannot join. The server cannot read its first message, so it
  turns the client away and keeps waiting for a player with the right key.

Known Bugs
==========
- The server runs one game. When a player leaves, the server closes the other player's game and
  stops, so it has to be started again for a new pair of players. Spectators are disconnected at
  the same time.
