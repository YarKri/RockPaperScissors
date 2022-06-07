from flask import Flask, render_template, request, Response
import websockets
import database_functions
import time
import asyncio
import logging
import threading
import os

import numpy
import cv2
from PIL import Image

app = Flask(__name__)

PORT = 8889
WEBSOCKET_PORT = 8890


@app.route('/login')
def login():
    user = request.args.get('user', '')
    password = request.args.get('password', '')
    logging.info(f'Login request for {user}')
    if database_functions.login(user, password):
        return Response(status=200)
    logging.info(f'Login request failed for {user}')
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
async def handle_play_request():
    global last_sid
    global game_lst
    bool_quit = request.args.get('quit', '')
    app.logger.info(f'handle_play_request: {last_sid=}, in game_lst: {last_sid in game_lst}')
    if bool_quit == 'True':
        app.logger.info(f'quit is True, removing {last_sid}')
        assert last_sid is not None
        await game_lst[last_sid][0][0].close()
        del game_lst[last_sid]
        return Response(status=200)
    if last_sid in game_lst and len(game_lst[last_sid]) == 1:
        session_id = last_sid
        app.logger.info(f'Opponent matched to a waiting user, {last_sid=}, {session_id=}')
    else:
        session_id = int(time.time()*100)
        last_sid = str(session_id)
        app.logger.info(f'User is waiting for opponent, {session_id=}')

    return Response(str(session_id), status=200)


def thread_websocket_server():
    asyncio.run(start_websocket_server())


async def start_websocket_server():
    async with websockets.serve(gme, "localhost", WEBSOCKET_PORT):
        await asyncio.Future()


async def update_un_gest(fut, websocket, sid, pid, value):
    msg = await websocket.recv()
    gesture = msg.split(',')[0]
    username = msg.split(',')[1]
    game_lst[sid][pid].append(gesture)
    game_lst[sid][pid].append(username)
    fut.set_result(value)


async def gme(websocket):
    global game_lst
    init = True
    frame_counter = 0
    countdown = 5
    async for message in websocket:
        if init:
            sid = message
            loop = asyncio.get_running_loop()
            if sid not in game_lst:
                game_lst[sid] = [[websocket, loop.create_future()]]
                pid = 0
            else:
                game_lst[sid].append([websocket, loop.create_future()])
                await asyncio.gather(game_lst[sid][0][0].send("start"), game_lst[sid][1][0].send("start"))
                pid = 1
            init = False

        elif countdown == 0:
            img = message
            await game_lst[sid][1-pid][0].send(img)
            fut = game_lst[sid][pid][1]
            await update_un_gest(fut, game_lst[sid][pid][0], sid, pid, True)
            opp_fut = game_lst[sid][1 - pid][1]
            await opp_fut
            gesture = game_lst[sid][pid][2]
            username = game_lst[sid][pid][3]
            opp_gesture = game_lst[sid][1-pid][2]
            opp_username = game_lst[sid][1-pid][3]

            if gesture == opp_gesture:
                await websocket.send("Tie, nobody")
            elif gesture == "No gesture was made!":
                await websocket.send(opp_username)
                database_functions.add_loss(username)
            elif opp_gesture == "No gesture was made!":
                await websocket.send(username)
                database_functions.add_win(username)
            elif gesture == 'Rock' and opp_gesture == 'Paper' or gesture == 'Scissors' and opp_gesture == 'Rock' or gesture == 'Paper' and opp_gesture == 'Scissors':
                await websocket.send(opp_username)
                database_functions.add_loss(username)
            else:
                await websocket.send(username)
                database_functions.add_win(username)

            # websocket.close()
        elif frame_counter == 10:
            frame_counter = 0
            countdown -= 1
            await websocket.send(str(countdown))
        else:
            img = message
            await game_lst[sid][1-pid][0].send(img)
            frame_counter += 1


if __name__ == "__main__":
    game_lst = {}  # {sid: [[websocket1, future, gesture1, username1],[websocket2, future, gesture2, username2]]...}
    last_sid = None
    try:
        ws_server_thread = threading.Thread(target=thread_websocket_server)
        ws_server_thread.start()
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=PORT)
    except Exception as e:
        print(f'{e}')
