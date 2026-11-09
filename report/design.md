Design
======

This is the draft of the Design section of the final report. It describes the message format the
team agreed on, so the client parts should be checked against the final client code before the
report is turned into a PDF.

Overview
--------

The project is split into a server and a client. One computer runs `pongServer.py` and each of the
two players runs `pongClient.py`. The clients never talk to each other directly. Each client sends
its own information to the server and the server hands it to the other client, so the server is the
only program both players have to be able to reach.

Each client runs the whole game by itself (the paddles, the ball and the score). The server does
not run any game logic. Its job is to pass each player's newest information to the other player so
the two games stay the same, and to look after the things that have to be shared, which are the
rematch and the leaderboard.

Why TCP
-------

The sockets are made with `socket.SOCK_STREAM`, which is TCP. We picked TCP for three reasons:

- TCP delivers every message and delivers them in order. The score is part of every update, so a
  lost or out of order message could leave the two players with different scores.
- TCP is connection based. The server gets one socket per player from `accept()`, which makes it
  easy to give each player their own thread and to know which player a message came from.
- The game only sends one small message per frame, so the extra speed UDP would give was not worth
  writing our own code to deal with lost packets.

Message framing
---------------

TCP is a stream of bytes and does not keep messages apart, so two messages can arrive stuck
together or one message can arrive in pieces. `networkHelpers.py` solves this for both programs:

- `sendMessage` turns a dictionary into JSON text, adds a newline to the end and sends it.
- `receiveMessage` keeps reading until it has seen a newline, returns that one message as a
  dictionary and saves any extra bytes for the next call.

Every message in the project is a dictionary sent this way, so neither program ever has to work
with raw bytes.

Connecting
----------

1. The server starts listening on port 19999 on address `0.0.0.0`, which lets clients on other
   computers connect and not only clients on the same computer.
2. A client connects and sends its first message, `{"initials": "NJ"}`. The first client to
   connect is given the left paddle and the second is given the right paddle.
3. The server waits until both players have connected. The first player's start screen says it is
   waiting for another player during this time.
4. The server sends each client `{"screenWidth": 640, "screenHeight": 480, "playerPaddle": "left"}`
   with that client's own paddle side. The screen size comes from the server so both games are
   always the same size, and sending it to both players together means both games start at the
   same moment.
5. The server starts one thread for each client.

Messages during the game
------------------------

Once per frame each client sends one update and the server sends back exactly one reply. Because
it is always one send followed by one receive, a client can never end up reading a reply that was
meant for a different frame.

The update a client sends:

| Key | What it holds |
| --- | --- |
| `paddleY` | The y position of this player's paddle |
| `moving` | Which way the paddle is moving, `"up"`, `"down"` or `""` |
| `ballX`, `ballY` | Where this client thinks the ball is |
| `lScore`, `rScore` | The score this client has for the left and right player |
| `sync` | How many frames this client has played |
| `playAgain` | True once this player has pressed space to ask for a rematch |

The reply from the server is one of three things:

| Reply | When it is sent |
| --- | --- |
| The other player's newest update | A normal frame |
| `{"waiting": true}` | The other player has not sent an update yet (first frame of a game only) |
| `{"reset": true}` | Both players asked for a rematch, so the client starts a new game |

Keeping the two games in sync
-----------------------------

Both clients move the ball themselves, so over time one game can get a frame or two ahead of the
other. Each client counts its frames in the `sync` variable and sends it with every update. When a
client gets the other player's update it compares the two numbers. If the other player's number is
larger, that player is further along, so this client copies their ball position and score. If this
client's number is larger it keeps its own. Both clients follow the same rule, so they always end
up agreeing with whichever game is further ahead.

Threads and shared data
-----------------------

The server has to listen to both players at the same time, and `receiveMessage` waits until a
message arrives. With only one thread the server would be stuck waiting on one player while the
other player's messages piled up. So the server starts one thread per client, and each thread runs
`handleClient` for its own socket.

Both threads read and write the same variables (each player's newest update, the rematch votes and
the leaderboard file). If both threads changed them at the same moment the data could be left half
updated. A single `threading.Lock` called `stateLock` protects all of it. A thread takes the lock,
saves its player's update, works out the reply and lets the lock go. The reply is sent after the
lock is released so that a slow connection for one player never holds up the other player.

Bonus features
--------------

Play Again:

- After a win the client shows "Space to play again". Pressing space sets `playAgain` to True in
  that client's updates.
- The server keeps a set of the sides that have asked. When both sides are in the set it clears the
  old game and answers that client with `{"reset": true}`.
- The other client is told on its very next update. Until it has been told, its update is thrown
  away, because it still holds the old winning score and would end the new game straight away.
- When a client gets the reset message it puts the score, the ball and both paddles back to the
  start.

Initials and wins:

- The start screen has an Initials box. The client cleans the text up (1 to 3 letters or numbers,
  upper case) and sends it as its first message.
- The server decides a game is over when both players' newest updates show the same player with
  more than 4 points. Waiting for both to agree stops a win from being counted when one game is a
  frame ahead of the other.
- The win is added to a dictionary of initials to wins and saved in `leaderboard.json`. A flag
  makes sure each game is only counted once, and the flag is cleared when a rematch starts.

Leaderboard webpage:

- The server also runs a small web server made with Python's `http.server` module. It runs in its
  own thread so it works next to the game.
- Any request gets back one HTML page with a table of initials and wins, sorted with the most wins
  at the top. The page reads `leaderboard.json` while holding `stateLock`, so it never reads the
  file while a game thread is writing it.
- It uses port 80 so the address is just the server's IP. Port 80 needs admin rights on some
  computers, so if it cannot be opened the server falls back to port 8080 and prints which port it
  used.
