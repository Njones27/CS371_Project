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

Known Bugs
==========
- The server doesn't work because the logic isn't yet written.
- The client doesn't speak to the server


