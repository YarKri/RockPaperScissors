import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import time
import pygame
import requests
import websockets
import cv2
from io import BytesIO
import numpy
from handtracking import HandTracking
import RockPaperScissors
from kivy.core.window import Window
import asyncio
import threading
import logging

# kivy.require('1.11.1')
pygame.mixer.init()

SERVER_URL = "http://localhost:8889"
WEBSOCKET_SERVER_URL = "ws://localhost:8890"
user = ''


def play_music():
    """
    Play theme song.
    """
    pygame.mixer.music.load("Soviet_Connection_(Theme_from[1]-[AudioTrimmer.com].mp3")
    pygame.mixer.music.play(-1)


def stop_music():
    """
    Stop playing theme song.
    """
    pygame.mixer.music.stop()


class MuteSwitch(GridLayout):
    def __init__(self, **kwargs):
        super(MuteSwitch, self).__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text="Mute Music:"))
        self.settings_sample = Switch(active=False)
        self.add_widget(self.settings_sample)
        self.settings_sample.bind(active=self.switch_callback)

    def switch_callback(self, switch_object, switch_value):
        if switch_value:
            stop_music()
        else:
            play_music()


class GridLayoutApp(App):
    def __init__(self):
        super().__init__()
        self.frame = (0, 0)
        self.last_time = 0
        self.layout = GridLayout(cols=3, rows=3)
        login_button = Button(text='Log In')
        login_button.bind(on_press=self.login_ui)
        signup_button = Button(text='Sign Up')
        signup_button.bind(on_press=self.signup_ui)
        quit_button = Button(text='Quit')
        quit_button.bind(on_press=exit)
        self.layout_matrix = [[Label(), Image(source="RPCLogo1.png", size_hint=(1, 5)), Label(text_size=(200, 350), font_size=15, halign='right', valign='top', outline_color=(1, 1, 1, 1), outline_width=2, color=(0, 0, 0, 1))],
                              [login_button, signup_button, quit_button],
                              [Label(), Image(opacity=0, source="onlinelogo.png"), MuteSwitch()]]

    def build(self):
        Window.borderless = True
        self.icon = "toppng.com-peace-hand-icon-1017x1589.png"
        self.title = "Rock Paper Scissors"
        for row in self.layout_matrix:
            for widget in row:
                self.layout.add_widget(widget)
        with self.layout.canvas.before:
            Color(0.2, 0.3, 0.2, 1)
            App.rect = Rectangle(size=(10000, 1000), pos=self.layout.pos)
        return self.layout

    def login(self, label, popup, username, password):
        global user
        user = username
        not_allowed = ";=*!%^&()"
        for char in not_allowed:
            if char in password or char in username:
                label.text = "Wrong password or username."
                return
        if len(password) == 0 or len(username) == 0:
            label.text = "Please enter all of your information."
        else:
            try:
                response = requests.get(f"{SERVER_URL}/login", params={"user": username, "password": password})
                if response.status_code == 404:
                    label.text = "Incorrect password or username."
                if response.status_code == 200:
                    popup.dismiss()
                    self.logged_in_ui(username)
            except:
                label.text = "Server down, try again later.\r\nSorry for the inconvenience."

    def login_ui(self, button=False):
        layout = GridLayout(cols=3, padding=10)

        un_label = Label(text="User Name:", size_hint=(1, 0.17))
        password_label = Label(text="Password: ", size_hint=(1, 0.17))
        close_button = Button(text="Cancel", size_hint=(1, 0.3))
        login_button = Button(text="Log In", size_hint=(1, 0.3))
        un_input = TextInput(multiline=False, size_hint=(1, 0.17))
        password_input = TextInput(multiline=False, size_hint=(1, 0.17), password=True)
        layout.add_widget(Label())
        layout.add_widget(Label())
        layout.add_widget(Label())

        layout.add_widget(un_label)
        layout.add_widget(un_input)
        layout.add_widget(Label(size_hint=(1, 0.17)))

        layout.add_widget(password_label)
        layout.add_widget(password_input)
        layout.add_widget(Label(size_hint=(1, 0.17)))

        layout.add_widget(Label())
        msg_label = Label(color=(1, 0, 0, 1))
        layout.add_widget(msg_label)
        layout.add_widget(Label())

        layout.add_widget(login_button)
        layout.add_widget(Label(size_hint=(1, 0.3)))
        layout.add_widget(close_button)

        popup = Popup(title='Log In', content=layout)
        popup.open()
        close_button.bind(on_press=popup.dismiss)
        login_button.bind(on_press=lambda _instance: self.login(msg_label, popup, un_input.text, password_input.text))

    def signup(self, label, inputs, username, password, verification, email):
        label.color = (1, 0, 0, 1)
        not_allowed = ";=*!%^&()"
        for char in not_allowed:
            if char in password or char in username:
                label.text = "Password or username must only\r\n     contain allowed characters."
                return
        if len(email) == 0 or len(password) == 0 or len(verification) == 0 or len(username) == 0:
            label.text = "Please enter all of the information."
        elif password != verification:
            label.text = "Password verification incorrect."
        elif "@" not in email or "." not in email:
            label.text = "Invalid email address."
        elif len(username) < 3 or len(username) > 10:
            label.text = "Username must be 3-10 characters long."
        else:
            try:
                response = requests.get(f"{SERVER_URL}/signup", params={"user": username, "password": password, "email":
                                        email})
                if response.status_code == 200:
                    label.text = "Your info has been saved."
                    label.color = (0, 1, 0, 1)
                    for inp in inputs:
                        inp.text = ""
                if response.status_code == 400:
                    label.text = response.text
            except:
                label.text = "Server down, try again later.\r\nSorry for the inconvenience."

    def signup_ui(self, button=False):
        layout = GridLayout(cols=3, padding=10)
        username_label = Label(text="User Name:", size_hint=(1, 0.2))
        password_label = Label(text="Password: ", size_hint=(1, 0.2))
        validate_label = Label(text="Validate Password: ", size_hint=(1, 0.2))
        email_label = Label(text="Email: ", size_hint=(1, 0.2))
        close_button = Button(text="Close", size_hint=(1, 0.3))
        signup_button = Button(text="Sign Up", size_hint=(1, 0.3))
        username_input = TextInput(multiline=False, size_hint=(1, 0.2))
        password_input = TextInput(multiline=False, size_hint=(1, 0.2), password=True)
        password_verification = TextInput(multiline=False, size_hint=(1, 0.2), password=True)
        email_input = TextInput(multiline=False, size_hint=(1, 0.2))

        layout.add_widget(Label())
        layout.add_widget(Label())
        layout.add_widget(Label())

        layout.add_widget(username_label)
        layout.add_widget(username_input)
        layout.add_widget(Label(size_hint=(1, 0.2)))

        layout.add_widget(password_label)
        layout.add_widget(password_input)
        layout.add_widget(Label(size_hint=(1, 0.2)))

        layout.add_widget(validate_label)
        layout.add_widget(password_verification)
        layout.add_widget(Label(size_hint=(1, 0.2)))

        layout.add_widget(email_label)
        layout.add_widget(email_input)
        layout.add_widget(Label(size_hint=(1, 0.2)))

        layout.add_widget(Label())
        msg_label = Label()
        layout.add_widget(msg_label)
        layout.add_widget(Label())

        layout.add_widget(signup_button)
        layout.add_widget(Label(size_hint=(1, 0.3)))
        layout.add_widget(close_button)

        popup = Popup(title='Sign Up', content=layout)
        popup.open()
        close_button.bind(on_press=popup.dismiss)
        signup_button.bind(on_press=lambda _instance: self.signup(msg_label, [username_input, password_input,
                                                                  password_verification, email_input],
                                                                  username_input.text, password_input.text,
                                                                  password_verification.text, email_input.text))

    def logged_in_ui(self, username):
        self.layout_matrix[0][2].text = f"Signed in as: {username}"
        self.layout_matrix[1][0].text = "Log Out"
        self.layout_matrix[1][0].unbind(on_press=self.login_ui)
        self.layout_matrix[1][0].bind(on_press=self.logout)
        self.layout_matrix[1][1].text = "Play"
        self.layout_matrix[1][1].unbind(on_press=self.signup_ui)
        self.layout_matrix[1][1].bind(on_press=self.play)
        self.layout_matrix[2][1].opacity = 1

    def img_to_texture(self, frame):
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        return texture

    def play(self, button=False):
        response = requests.get(f"{SERVER_URL}/play", params={"quit": False}).text
        sid = response
        self.layout_matrix[2][0].text = "Searching for game..."
        self.layout_matrix[1][1].disabled = True
        self.layout_matrix[1][0].bind(on_press=self.quit_while_queueing)
        self.layout_matrix[1][2].bind(on_press=self.quit_while_queueing)
        gme = threading.Thread(target=self.play_thread, args=(sid,))
        gme.start()

    def play_thread(self, sid):
        Clock.schedule_interval(self.update_frame, 0.1)
        asyncio.run(self.game(sid))

    def ui_game_start(self):
        self.layout_matrix[1][0].disabled = True
        self.layout_matrix[1][2].disabled = True
        self.layout_matrix[2][0].text = ""

    def update_frame(self, dt):
        tme = self.frame[0]
        opp_img = self.frame[1]
        if self.last_time != tme:
            opp_img = self.img_to_texture(opp_img)
            self.layout_matrix[0][1].texture = opp_img

    async def game(self, sid):
        try:
            async with websockets.connect(WEBSOCKET_SERVER_URL) as ws:
                await ws.send(sid)
                msg = await ws.recv()
                if msg == "start":
                    blur = False
                    cntdwn = 5
                    logging.info("Game started")
                    self.ui_game_start()
                    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    tracker = HandTracking()
                    while True:
                        success, img = cap.read()
                        landmark_lst = tracker.find_lm_positions(img)
                        if landmark_lst and blur:
                            RockPaperScissors.blur_hand(img, landmark_lst)
                        RockPaperScissors.put_username("", img)
                        RockPaperScissors.put_pos(cntdwn, img)
                        img = self.compress_img(img)
                        await ws.send(img)
                        msg = await ws.recv()
                        logging.info(f"MSG: {msg if len(msg) == 1 else 'image'}")
                        if msg == "4":
                            blur = True
                            cntdwn = 4
                        elif msg == "3":
                            cntdwn = 3
                        elif msg == "2":
                            cntdwn = 2
                        elif msg == "1":
                            cntdwn = 1
                        elif msg == "0":
                            break
                        elif success:
                            opp_img = self.decompress_img(msg)
                            self.last_time = self.frame[0]
                            self.frame = (int(time.time()*100), opp_img)

                    success, img = cap.read()
                    img = tracker.draw_hands(img)
                    landmark_lst = tracker.find_lm_positions(img)
                    cap.release()
                    if landmark_lst:
                        gesture = RockPaperScissors.identify_r_p_s(landmark_lst)
                    else:
                        gesture = "No gesture was made!"
                    cv2.putText(img, gesture, (100, 400), cv2.FONT_ITALIC, 1, (0, 0, 255), 3)
                    img = self.compress_img(img)
                    await ws.send(img)
                    opp_img = self.decompress_img(await ws.recv())
                    await ws.send(gesture)
                    await ws.send(user)
                    winner = await ws.recv()
                    self.last_time = self.frame[0]
                    self.frame = (int(time.time() * 100), opp_img)
                    await asyncio.sleep(1)
                    cv2.putText(opp_img, f'{winner} wins!', (10, 200), cv2.FONT_ITALIC, 4, (0, 0, 255), 5)
                    self.last_time = self.frame[0]
                    self.frame = (int(time.time() * 100), opp_img)
                    await asyncio.sleep(3)
                    await ws.close()
        except Exception as e:
            print(e)
            self.layout_matrix[2][0].text = " Error, try\r\nagain later."
        # await ws.close()
        self.layout_matrix[1][0].disabled = False
        self.layout_matrix[1][1].disabled = False
        self.layout_matrix[1][2].disabled = False
        self.layout_matrix[1][0].unbind(on_press=self.quit_while_queueing)
        self.layout_matrix[1][2].unbind(on_press=self.quit_while_queueing)

    def compress_img(self, cv_img, quality=95):
        buffer = BytesIO()
        # cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        success, jpg = cv2.imencode('.jpg', cv_img, encode_param)
        if not success:
            return None
        buffer.write(jpg.tobytes())
        buffer.seek(0)
        return buffer

    def decompress_img(self, buffer):
        buffer = BytesIO(buffer).read()
        buffer = numpy.frombuffer(buffer, dtype=numpy.byte)
        return cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    def logout(self, button=False):
        """
        Reverts UI to its original state (before user logged in).
        """
        global user
        user = ''
        self.layout_matrix[0][2].text = ""
        self.layout_matrix[1][0].text = "Log In"
        self.layout_matrix[1][1].text = "Sign Up"
        self.layout_matrix[1][0].unbind(on_press=self.logout)
        self.layout_matrix[1][0].bind(on_press=self.login_ui)
        self.layout_matrix[1][1].unbind(on_press=self.play)
        self.layout_matrix[1][1].bind(on_press=self.signup_ui)
        self.layout_matrix[2][0].text = ""
        self.layout_matrix[2][1].opacity = 0

    def quit_while_queueing(self, button=False):
        requests.get(f"{SERVER_URL}/play", params={"quit": True})
        self.layout_matrix[1][0].unbind(on_press=self.quit_while_queueing)
        self.layout_matrix[1][2].unbind(on_press=self.quit_while_queueing)
        self.layout_matrix[1][1].disabled = False


root = GridLayoutApp()
play_music()
root.run()
