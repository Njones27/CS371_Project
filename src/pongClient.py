# =================================================================================================
# Contributing Authors:	    Ryan Rice, Nathan Jones
# Email Addresses:          rlri231@uky.edu, njjo227@uky.edu
# Date:                     11.26.2026
# Purpose:                  The client side of the game. The start screen collects the server address,
#                           initials, username and password, then the game loop sends this player's
#                           paddle, ball, score and sync to the server every frame and uses the reply to
#                           draw the opponent (or both players, when watching as a spectator)
# Misc:                     Run from inside src/ so the fonts, sounds and images in ./assets are found.
#                           Every message goes through networkHelpers.py, so it is encrypted
# =================================================================================================

# sendMessage(socket.socket,data: dict)
# receiveMessage(socket.socket) -> dict
from networkHelpers import sendMessage, receiveMessage
import pygame
import tkinter as tk
import sys
import socket

from assets.code.helperCode import *

def quitGame(client:socket.socket, reason:str) -> None:
    # Author:       Ryan Rice
    # Purpose:      Shuts the game down cleanly. Used both when the player closes the window and
    #               when the server stops answering, so the program always closes the same way
    # Pre:          client is the socket connected to the server and pygame has been started.
    #               reason is a short message saying why the game is closing
    # Post:         reason is printed, the socket is closed, the pygame window is closed and the
    #               program ends. The server sees the connection close
    print(reason)
    # Closing the socket tells the server this player is gone instead of leaving it waiting
    client.close()
    pygame.quit()
    sys.exit()

# This is the main game loop.  For the most part, you will not need to modify this.  The sections
# where you should add to the code are marked.  Feel free to change any part of this project
# to suit your needs.
def playGame(screenWidth:int, screenHeight:int, playerPaddle:str, client:socket.socket) -> None:
    # Author:       Course template (game logic and drawing). Ryan Rice (sending and receiving
    #               updates, sync, disconnect handling, spectator mode). Nathan Jones (Play Again)
    # Purpose:      Runs the game at 60 frames a second. Every frame it reads the keys, moves the
    #               paddles and ball, draws the screen, sends this player's update to the server
    #               and uses the server's reply to move the opponent and stay in sync. A spectator
    #               ignores the keys and copies both paddles, the ball and the score from the server
    # Pre:          joinServer has connected client to the server and received screenWidth and
    #               screenHeight (pixels) and playerPaddle ("left", "right" or "spectator")
    # Post:         Never returns normally. The loop runs until quitGame closes the socket and ends
    #               the program, either because the window was closed or the server went away

    # Pygame inits
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.init()

    # Constants
    WHITE = (255,255,255)
    clock = pygame.time.Clock()
    scoreFont = pygame.font.Font("./assets/fonts/pong-score.ttf", 32)
    winFont = pygame.font.Font("./assets/fonts/visitor.ttf", 48)
    pointSound = pygame.mixer.Sound("./assets/sounds/point.wav")
    bounceSound = pygame.mixer.Sound("./assets/sounds/bounce.wav")

    # Display objects
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    winMessage = pygame.Rect(0,0,0,0)
    topWall = pygame.Rect(-10,0,screenWidth+20, 10)
    bottomWall = pygame.Rect(-10, screenHeight-10, screenWidth+20, 10)
    centerLine = []
    for i in range(0, screenHeight, 10):
        centerLine.append(pygame.Rect((screenWidth/2)-5,i,5,5))

    # Paddle properties and init
    paddleHeight = 50
    paddleWidth = 10
    paddleStartPosY = (screenHeight/2)-(paddleHeight/2)
    leftPaddle = Paddle(pygame.Rect(10,paddleStartPosY, paddleWidth, paddleHeight))
    rightPaddle = Paddle(pygame.Rect(screenWidth-20, paddleStartPosY, paddleWidth, paddleHeight))

    ball = Ball(pygame.Rect(screenWidth/2, screenHeight/2, 5, 5), -5, 0)

    if playerPaddle == "left":
        opponentPaddleObj = rightPaddle
        playerPaddleObj = leftPaddle
    else:
        opponentPaddleObj = leftPaddle
        playerPaddleObj = rightPaddle

    # Spectator mode. Every client after the two players is told "spectator" by the server. A
    # spectator ignores the keyboard and copies both paddles, the ball and the score from the server.
    # It still lands in the else branch above, but its "player" paddle is never moved by the keys
    spectator = playerPaddle == "spectator"
    # Small label drawn at the bottom of a spectator's window
    spectatorSurface = pygame.font.Font("./assets/fonts/visitor.ttf", 20).render("Spectating", False, WHITE)

    lScore = 0
    rScore = 0

    sync = 0

    # Play Again. playAgain turns True once this player presses space after a win. It needs to be
    # sent to the server as "playAgain": playAgain in the update dictionary
    playAgain = False
    # The server's latest answer. Starts empty so the reset check at the bottom of the loop is
    # safe to run before the first answer arrives
    reply = {}

    while True:
        # Wiping the screen
        screen.fill((0,0,0))

        # Getting keypress events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitGame(client, "You closed the game")
            # "and not spectator" means a spectator's keys do nothing, so it can only watch
            elif event.type == pygame.KEYDOWN and not spectator:
                if event.key == pygame.K_DOWN:
                    playerPaddleObj.moving = "down"

                elif event.key == pygame.K_UP:
                    playerPaddleObj.moving = "up"

                # Space asks for a rematch, but it only counts once someone has already won
                elif event.key == pygame.K_SPACE and (lScore > 4 or rScore > 4):
                    playAgain = True

            elif event.type == pygame.KEYUP and not spectator:
                playerPaddleObj.moving = ""

        # =========================================================================================
        # Your code here to send an update to the server on your paddle's information,
        # where the ball is and the current score.
        # Feel free to change when the score is updated to suit your needs/requirements
        
        
        # =========================================================================================

        # Update the player paddle and opponent paddle's location on the screen
        for paddle in [playerPaddleObj, opponentPaddleObj]:
            if paddle.moving == "down":
                if paddle.rect.bottomleft[1] < screenHeight-10:
                    paddle.rect.y += paddle.speed
            elif paddle.moving == "up":
                if paddle.rect.topleft[1] > 10:
                    paddle.rect.y -= paddle.speed

        # If the game is over, display the win message
        if lScore > 4 or rScore > 4:
            winText = "Player 1 Wins! " if lScore > 4 else "Player 2 Wins! "
            textSurface = winFont.render(winText, False, WHITE, (0,0,0))
            textRect = textSurface.get_rect()
            textRect.center = ((screenWidth/2), screenHeight/2)
            winMessage = screen.blit(textSurface, textRect)

            # Under the win message, tell the player how to ask for a rematch. Once they have
            # pressed space the text changes so they know it worked
            againText = "Waiting for opponent" if playAgain else "Space to play again"
            # A spectator cannot vote for a rematch, so it is only told what is happening
            if spectator:
                againText = "Waiting for the players"
            againSurface = winFont.render(againText, False, WHITE, (0,0,0))
            screen.blit(againSurface, againSurface.get_rect(center=(screenWidth/2, screenHeight/2 + 50)))
        else:

            # ==== Ball Logic =====================================================================
            ball.updatePos()

            # If the ball makes it past the edge of the screen, update score, etc.
            if ball.rect.x > screenWidth:
                lScore += 1
                pointSound.play()
                ball.reset(nowGoing="left")
            elif ball.rect.x < 0:
                rScore += 1
                pointSound.play()
                ball.reset(nowGoing="right")
                
            # If the ball hits a paddle
            if ball.rect.colliderect(playerPaddleObj.rect):
                bounceSound.play()
                ball.hitPaddle(playerPaddleObj.rect.center[1])
            elif ball.rect.colliderect(opponentPaddleObj.rect):
                bounceSound.play()
                ball.hitPaddle(opponentPaddleObj.rect.center[1])
                
            # If the ball hits a wall
            if ball.rect.colliderect(topWall) or ball.rect.colliderect(bottomWall):
                bounceSound.play()
                ball.hitWall()
            
            pygame.draw.rect(screen, WHITE, ball)
            # ==== End Ball Logic =================================================================

        # Drawing the dotted line in the center
        for i in centerLine:
            pygame.draw.rect(screen, WHITE, i)
        
        # Drawing the player's new location
        for paddle in [playerPaddleObj, opponentPaddleObj]:
            pygame.draw.rect(screen, WHITE, paddle)

        pygame.draw.rect(screen, WHITE, topWall)
        pygame.draw.rect(screen, WHITE, bottomWall)
        scoreRect = updateScore(lScore, rScore, screen, WHITE, scoreFont)
        if spectator:
            screen.blit(spectatorSurface, spectatorSurface.get_rect(center=(screenWidth/2, screenHeight - 30)))
        pygame.display.update()
        clock.tick(60)
        
        # This number should be synchronized between you and your opponent.  If your number is larger
        # then you are ahead of them in time, if theirs is larger, they are ahead of you, and you need to
        # catch up (use their info)
        sync += 1
        # =========================================================================================
        # Send your server update here at the end of the game loop to sync your game with your
        # opponent's game
        # create the update frame to send to the server 
        update = {
            "paddleY":playerPaddleObj.rect.y,
            "moving": playerPaddleObj.moving,
            "ballX": ball.rect.x,
            "ballY": ball.rect.y,
            "ballXVel": ball.xVel,
            "ballYVel": ball.yVel,
            "lScore": lScore,
            "rScore": rScore,
            "sync": sync,
            "playAgain": playAgain

        }
        # If the server closed or crashed, sending or receiving raises an exception instead of
        # returning. ConnectionError comes from receiveMessage when the server hangs up, OSError covers
        # other network errors (like a reset connection) and ValueError covers a half sent message
        try:
            if spectator:
                # A spectator has nothing to report, it only asks for the current game
                sendMessage(client, {"spectator": True})
            else:
                sendMessage(client,update)
            # recieve opponents data
            reply = receiveMessage(client)
        except (ConnectionError, OSError, ValueError) as e:
            quitGame(client, f"Lost connection to the server, closing the game: {e}")

        if spectator:
            # The reply is {"left": <left player's update>, "right": <right player's update>}. Either can
            # be None if that player has not sent an update yet (the start of a game or a rematch)
            players = [reply.get("left"), reply.get("right")]
            for state, paddle in zip(players, [leftPaddle, rightPaddle]):
                if state:
                    paddle.rect.y = state["paddleY"]
                    paddle.moving = state["moving"]
            sent = [state for state in players if state]
            if sent:
                # Same idea as Client Step 11: the player with the bigger sync number is furthest
                # along, so the spectator copies their ball and score
                ahead = max(sent, key=lambda state: state["sync"])
                ball.rect.x = ahead["ballX"]
                ball.rect.y = ahead["ballY"]
                ball.xVel = ahead["ballXVel"]
                ball.yVel = ahead["ballYVel"]
                lScore = ahead["lScore"]
                rScore = ahead["rScore"]
                sync = ahead["sync"]
        # update opponenet paddle object if reply was received
        elif "paddleY" in reply:
            opponentPaddleObj.rect.y = reply["paddleY"]
            opponentPaddleObj.moving = reply["moving"]
            # if opponent is ahead use their information to update game data
            # ignores on "waiting" since paddleY update is not sent for a waiting reply
            if reply["sync"] > sync:
                ball.rect.x = reply["ballX"]
                ball.rect.y = reply["ballY"]
                lScore = reply["lScore"]
                rScore = reply["rScore"]
                sync = reply["sync"]
                ball.xVel = reply["ballXVel"]
                ball.yVel = reply["ballYVel"]
         

        # =========================================================================================

        # Play Again. When the server says both players want a rematch, put everything back to how
        # it was at the start of playGame. .get is used because most replies do not have a "reset" key
        if reply.get("reset"):
            lScore, rScore, sync, playAgain = 0, 0, 0, False
            ball.reset(nowGoing="left")
            leftPaddle.rect.y = rightPaddle.rect.y = paddleStartPosY




# This is where you will connect to the server to get the info required to call the game loop.  Mainly
# the screen width, height and player paddle (either "left" or "right")
# If you want to hard code the screen's dimensions into the code, that's fine, but you will need to know
# which client is which
def joinServer(ip:str, port:str, initials:str, username:str, password:str, errorLabel:tk.Label, app:tk.Tk) -> None:
    # Author:       Ryan Rice (connecting, receiving the setup, login). Nathan Jones (initials)
    # Purpose:      Runs when the Join button is clicked. Checks what the player typed, connects to
    #               the server, sends the initials, username and password, waits for the screen size
    #               and paddle side, then starts the game
    # Pre:          The start screen is open. ip, port, initials, username and password are what the
    #               player typed. errorLabel is the label under the Join button and app is the window
    # Post:         If joining worked, the start window is hidden and playGame runs. If anything
    #               failed (bad input, no server, wrong password) errorLabel says why, the socket is
    #               closed and the start screen stays open so the player can try again

    # Clean up the initials before connecting. strip() removes spaces, upper() makes "nj" and "NJ"
    # count as the same player, and [:3] keeps at most 3 characters
    initials = initials.strip().upper()[:3]
    # isalnum() is False for an empty box or symbols, so the player cannot join without real initials
    if not initials.isalnum():
        errorLabel.config(text="Enter 1 to 3 letters or numbers for your initials")
        errorLabel.update()
        return

    # Registration and login. Both boxes have to be filled in before the player can join
    username = username.strip()
    if not username or not password:
        errorLabel.config(text="Enter a username and a password")
        errorLabel.update()
        return

    # Create a socket and connect to the server
    # You don't have to use SOCK_STREAM, use what you think is best
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # convert port to usable int
    try:
        client.connect((ip,int(port)))
    except (OSError, ValueError) as e:
      errorLabel.config(text=f"Could not connect: {e}")
      errorLabel.update()
      # Close the socket that failed so a fresh one is made if the player clicks Join again
      client.close()
      return
    errorLabel.config(text="Connected, wating for another player...")
    errorLabel.update()

    # Tell the server who this player is so wins can be saved under these initials, along with the
    # username and password for the login. The server reads this first. A wrong password is answered
    # right away with an error, otherwise the screen size and paddle side come once both players joined
    sendMessage(client, {"initials": initials, "username": username, "password": password})

    # Get the required information from your server (screen width, height & player paddle, "left or "right)
    #receive message function -- send message function must be implemented server side to send message,
    # client side will also need a send message function to send information to the server
    try:
        data = receiveMessage(client)
    except(OSError,ValueError) as e:
        errorLabel.config(text=f"Could not receive data: {e}")
        errorLabel.update()
        client.close()
        return
    # The server turned this player away, for example because of a wrong password. Show why and stay
    # on the start screen so the player can fix it and click Join again
    if "error" in data:
        errorLabel.config(text=data["error"])
        errorLabel.update()
        client.close()
        return
    # data will be sent in the format {"screenWidth" : ###,"screenHeight" : ###, "playerPaddle" : "left" }
    screenWidth = data["screenWidth"] # int
    screenHeight = data["screenHeight"] # int
    playerPaddle = data["playerPaddle"] # left or right string
    '''
    # If you have messages you'd like to show the user use the errorLabel widget like so
    errorLabel.config(text=f"Some update text. You input: IP: {ip}, Port: {port}")
    # You may or may not need to call this, depending on how many times you update the label
    errorLabel.update()     
    '''

    # Close this window and start the game with the info passed to you from the server
    app.withdraw()     # Hides the window (we'll kill it later)
    playGame(screenWidth, screenHeight, playerPaddle, client)  # User will be either left or right paddle
    app.quit()         # Kills the window


# This displays the opening screen, you don't need to edit this (but may if you like)
def startScreen() -> None:
    # Author:       Course template. Nathan Jones (Initials box). Ryan Rice (Username and Password boxes)
    # Purpose:      Builds the start window with the logo, the Server IP, Server Port, Initials,
    #               Username and Password boxes, the Join button and the message label
    # Pre:          The program was started from inside src/ so ./assets/images/logo.png can be found
    # Post:         The window stays open until the game starts or it is closed. Clicking Join calls
    #               joinServer with what the player typed
    app = tk.Tk()
    app.title("Server Info")

    image = tk.PhotoImage(file="./assets/images/logo.png")

    titleLabel = tk.Label(image=image)
    titleLabel.grid(column=0, row=0, columnspan=2)

    ipLabel = tk.Label(text="Server IP:")
    ipLabel.grid(column=0, row=1, sticky="W", padx=8)

    ipEntry = tk.Entry(app)
    ipEntry.grid(column=1, row=1)

    portLabel = tk.Label(text="Server Port:")
    portLabel.grid(column=0, row=2, sticky="W", padx=8)

    portEntry = tk.Entry(app)
    portEntry.grid(column=1, row=2)

    # Initials box for the leaderboard, built the same way as the IP and port boxes
    initialsLabel = tk.Label(text="Initials:")
    initialsLabel.grid(column=0, row=3, sticky="W", padx=8)

    initialsEntry = tk.Entry(app)
    initialsEntry.grid(column=1, row=3)

    # Username and password boxes for registration and login. show="*" hides the password as it is typed
    usernameLabel = tk.Label(text="Username:")
    usernameLabel.grid(column=0, row=4, sticky="W", padx=8)

    usernameEntry = tk.Entry(app)
    usernameEntry.grid(column=1, row=4)

    passwordLabel = tk.Label(text="Password:")
    passwordLabel.grid(column=0, row=5, sticky="W", padx=8)

    passwordEntry = tk.Entry(app, show="*")
    passwordEntry.grid(column=1, row=5)

    # The Join button and error label sit under all the boxes
    errorLabel = tk.Label(text="")
    errorLabel.grid(column=0, row=7, columnspan=2)

    joinButton = tk.Button(text="Join", command=lambda: joinServer(ipEntry.get(), portEntry.get(), initialsEntry.get(),
                                                                   usernameEntry.get(), passwordEntry.get(), errorLabel, app))
    joinButton.grid(column=0, row=6, columnspan=2)

    app.mainloop()

if __name__ == "__main__":
    startScreen()
    
    # Uncomment the line below if you want to play the game without a server to see how it should work
    # the startScreen() function should call playGame with the arguments given to it by the server this is
    # ----------------------
    # here for demo purposes only    
    #skips network client
    #playGame(640, 480,"left",socket.socket(socket.AF_INET, socket.SOCK_STREAM))
