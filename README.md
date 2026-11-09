# CS371_Project
Repo for the CS371 Networking course project

Contact Info
============

Group Members & Email Addresses:

    Person 1, person1@uky.edu
    Person 2, person2@uky.edu

Versioning
==========

Github Link: 

General Info
============
This is a two player Pong game that is played over the network. One computer runs the server and
each player runs the client. The server passes each player's paddle, ball and score information to
the other player so both screens show the same game.

Starting the server:

1. Open a terminal in the `src` folder.
2. Run `python3 pongServer.py`. On Mac or Linux use `sudo python3 pongServer.py` so the leaderboard
   webpage is able to use port 80.
3. Leave it running. The game uses port 19999.

Joining a game:

1. Open a terminal in the `src` folder. The client has to be started from this folder because it
   loads its fonts, sounds and logo from `./assets`.
2. Run `python3 pongClient.py`.
3. Type in the server's IP address, the port `19999` and your initials, then click Join. If the
   server is on the same computer use `127.0.0.1`. If it is on another computer use the IP address
   of the computer running the server, which you can find by running `ipconfig` on Windows or
   `ifconfig` on Mac and Linux.
4. The first player to join is the left paddle and the second player is the right paddle. The
   first player's window says it is waiting for another player, and the game opens on both
   computers once the second player has joined.

Playing:

- The up and down arrow keys move your paddle.
- The first player to reach 5 points wins.

Playing on two computers:

- Both computers need to be able to reach each other, for example by both being on the UK VPN.
- The firewall on the server's computer has to allow incoming connections to Python.

Install Instructions
====================

Run the following line to install the required libraries for this project:

`pip3 install -r requirements.txt`

Bonus Features
==============

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

Known Bugs
==========
- The server doesn't work because the logic isn't yet written.
- The client doesn't speak to the server


