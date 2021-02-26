# -*- coding: utf-8 -*-
import json
import socket
import threading
import messages
import model
import view

BUFFER_SIZE = 2 ** 10


class Application(object):
    instance = None

    def __init__(self, args):
        self.args = args
        self.closing = False
        self.host = None
        self.port = None
        self.receive_worker = None
        self.sock = None
        self.username = None
        self.ui = view.TacticalFightUI(self)
        Application.instance = self

    def execute(self):
        if not self.ui.show():
            return
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))

        except (socket.error, OverflowError):
            self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
            return
        self.receive_worker = threading.Thread(target=self.receive)
        self.receive_worker.start()
        self.ui.loop()

    def receive(self):
        temp = True
        while True:
            try:
                message = model.Message(**json.loads(self.receive_all()))
            except (ConnectionAbortedError, ConnectionResetError):
                if not self.closing:
                    self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
                return

            if message:
                if message.message == messages.WAIT:
                    self.ui.block_ui()
                elif message.message == messages.MOVE:
                    self.ui.begin_turn()
                    if temp:
                        temp = False
                        message = model.Message(message=None, quit=False, end_turn=False)
                        try:
                            self.sock.sendall(message.marshal())
                        except (ConnectionAbortedError, ConnectionResetError):
                            if not self.closing:
                                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)
                elif message.message == messages.LOSE:
                    self.ui.show_info("Your game ended", messages.LOSE)
                    self.ui.on_closing()
                    return
                elif message.message == messages.WIN:
                    self.ui.show_info("Your game ended", messages.WIN)
                    self.ui.on_closing()
                    return

                elif message.message == messages.HELLO:
                    self.send_username()
                    self.ui.block_ui()
                elif message.message == messages.WRONG_NAME:
                    self.ui.alert(messages.ERROR, "Existing username")
                    self.ui.on_closing()
                elif message.message == messages.SAVED:
                    self.ui.show_info("Game Saved", "Game Saved Successfully")
                else:
                    self.ui.game_matrix = message.message
                    self.ui.rewrite_text()

    def end_turn(self):
        message = model.Message(message=None, quit=False, end_turn=True)
        try:
            self.sock.sendall(message.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def move(self):
        message = model.Message(message=self.ui.game_matrix)
        try:
            self.sock.sendall(message.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def save_game(self):
        message = model.Message(message=None, quit=False, end_turn=False, save=True)
        try:
            self.sock.sendall(message.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def send_username(self):
        message = model.Message(username=self.username, message=None, quit=False)
        try:
            self.sock.sendall(message.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def surrender(self):
        message = model.Message(message=None, quit=True, end_turn=False)
        try:
            self.sock.sendall(message.marshal())
        except (ConnectionAbortedError, ConnectionResetError):
            if not self.closing:
                self.ui.alert(messages.ERROR, messages.CONNECTION_ERROR)

    def receive_all(self):
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += self.sock.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def exit(self):
        self.closing = True
        try:
            self.sock.sendall(model.Message(message="", quit=True).marshal())
        except (ConnectionResetError, ConnectionAbortedError, OSError):
            print(messages.CONNECTION_ERROR)
        finally:
            self.sock.close()
