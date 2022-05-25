from flask import Flask, render_template, request, Response
import websockets
import database_functions
import time
import asyncio
import threading
from game import Game
app = Flask(__name__)

game_lst = {}    # {[[websocket1, gesture1, username1],[websocket2, gesture2, username2]]...}
last_sid = 0

PORT = 8889
WEBSOCKET_PORT = 8890


@app.route('/login')
def login():
    user = request.args.get('user', '')
    password = request.args.get('password', '')
    if database_functions.login(user, password):
        return Response(status=200)
    return Response("Not Found", status=404)


@app.route('/signup')
def signup():
    user = request.args.get('user', '')
    password = request.args.get('password', '')
    email = request.args.get('email', '')
    if not database_functions.signup(user, password, email):
        return Response("Username already taken.", status=400)
    return Response(status=200)


@app.route('/play')
def handle_play_request():
    global last_sid
    global game_lst
    bool_quit = request.args.get('quit', '')
    if bool_quit == 'True':
        game_lst[last_sid][0].close()
        del game_lst[last_sid]
        return

    if last_sid in game_lst and len(game_lst[last_sid]) == 1:
        session_id = last_sid
    else:
        session_id = int(time.time()*100)
        last_sid = session_id

    return Response(str(session_id), status=200)


def thread_websocket_server():
    asyncio.run(start_websocket_server())


async def start_websocket_server():
    # start_server = websockets.serve(init_game, "localhost", 8890)
    async with websockets.serve(gme, "localhost", WEBSOCKET_PORT):
        await asyncio.Future()
    # asyncio.get_event_loop().run_until_complete(start_server)
    # asyncio.get_event_loop().run_forever()


async def gme(websocket):
    global game_lst
    init = True
    frame_counter = 0
    countdown = 4
    async for message in websocket:
        if init:
            sid = message
            if sid not in game_lst:
                game_lst[sid] = [[websocket]]
                pid = 0
            else:
                game_lst[sid].append([websocket])
                await game_lst[sid][0].send("start")
                await game_lst[sid][1].send("start")
                pid = 1
            init = False
        elif countdown == -1:
            img = await websocket.recv()
            await game_lst[sid][1-pid].send(img)

            gesture = await websocket.recv()
            game_lst[sid][pid].append(gesture)
            username = await websocket.recv()
            game_lst[sid][pid].append(gesture)
            opp_gesture = game_lst[sid][1-pid][1]
            opp_username = game_lst[sid][1-pid][2]

            if gesture == opp_gesture:
                websocket.send("Tie, nobody")
            elif gesture == "No gesture was made!":
                websocket.send(opp_username)
                database_functions.add_loss(username)
            elif opp_gesture == "No gesture was made!":
                websocket.send(username)
                database_functions.add_win(username)
            elif gesture == 'Rock' and opp_gesture == 'Paper' or gesture == 'Scissors' and opp_gesture == 'Rock' or gesture == 'Paper' and opp_gesture == 'Scissors':
                websocket.send(opp_username)
                database_functions.add_loss(username)
            else:
                websocket.send(username)
                database_functions.add_win(username)

            # websocket.close()
        elif frame_counter == 10:
            frame_counter = 0
            countdown -= 1
            websocket.send(countdown)
        else:
            img = await websocket.recv()
            await game_lst[sid][1-pid].send(img)
            frame_counter += 1

'''
def handle_game(websocket):
    global games
    pid = 0
    add = True
    for gm in games:
        if gm.state == 'Waiting for player 2.':
            gm.player2_found(websocket)
            add = False
            break
    if add:
        games[Game(websocket)] = []
        pid = 1
    gm = find_game(websocket)
    async for msg in websocket:
        if gm.state == 'Game.':
            games[gm].append(msg)
            websocket.send(games[gm][pid])


def find_game(websocket):
    for gm in games:
        if gm.contains(websocket):
            return gm
'''     # do not use?

if __name__ == "__main__":
    try:
        ws_server_thread = threading.Thread(target=thread_websocket_server)
        ws_server_thread.start()
        app.run(debug=True, host='0.0.0.0', port=8889)
    except Exception as e:
        print(f'unable to open port {e}')
