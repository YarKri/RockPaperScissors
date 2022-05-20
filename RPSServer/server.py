from flask import Flask, render_template, request, Response
import websockets
import database_functions
import time
import asyncio
import threading
app = Flask(__name__)

game_lst = {}
last_sid = 0


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

    # a comment
    if last_sid in game_lst and len(game_lst[last_sid]) == 1:
        session_id = last_sid
    else:
        session_id = int(time.time()*100)
        last_sid = session_id
    start_thread = threading.Thread(target=start_websocket_server)
    start_thread.start()
    return Response(str(session_id), status=200)


def start_websocket_server():
    start_server = websockets.serve(init_game, "localhost", 8889)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()  # ?


async def init_game(websocket):
    global game_lst
    async for message in websocket:
        # sid = websocket.recv()
        sid = message
        if sid not in game_lst:
            game_lst[sid] = [websocket]
        else:
            game_lst[sid].append(websocket)
            await game_lst[sid][0].send("start")
            await game_lst[sid][1].send("start")
            await game(game_lst[sid][0], game_lst[sid][1])


async def game(websocket1, websocket2):
    for cnt_dwn in range(4, -1, -1):
        for i in range(12):
            await send_images(websocket1, websocket2)
        websocket1.send(str(cnt_dwn))
        websocket2.send(str(cnt_dwn))
    await send_images(websocket1, websocket2)
    gesture1 = await websocket1.recv()
    gesture2 = await websocket2.recv()
    user1 = await websocket1.recv()
    user2 = await websocket2.recv()
    if gesture1 == gesture2:
        websocket1.send("Tie, nobody")
        websocket2.send("Tie, nobody")
    elif gesture1 == "No gesture was made!" and gesture2 != gesture1:
        websocket2.send(user2)
        websocket1.send(user2)
        database_functions.add_win(user2)
        database_functions.add_loss(user1)
    elif gesture2 == "No gesture was made!" and gesture1 != gesture2:
        websocket1.send(user1)
        websocket2.send(user1)
        database_functions.add_win(user1)
        database_functions.add_loss(user2)
    elif gesture1 == 'Rock' and gesture2 == 'Paper' or gesture1 == 'Scissors' and gesture2 == 'Rock' or gesture1 == 'Paper' and gesture2 == 'Scissors':
        websocket1.send(user2)
        websocket2.send(user2)
        database_functions.add_win(user2)
        database_functions.add_loss(user1)
    else:
        websocket1.send(user1)
        websocket2.send(user1)
        database_functions.add_win(user1)
        database_functions.add_loss(user2)


async def send_images(websocket1, websocket2):
    img1 = await websocket1.recv()
    img2 = await websocket2.recv()
    websocket1.send(img2)
    websocket2.send(img1)


if __name__ == "__main__":
    try:
        app.run(debug=True, host='0.0.0.0', port=8889)
    except:
        print('unable to open port')
