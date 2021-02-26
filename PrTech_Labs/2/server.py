# -*- coding: utf-8 -*-
import json
import socket
import sys
import threading
import model

BUFFER_SIZE = 2 ** 10
CLOSING = "Application closing..."
CONNECTION_ABORTED = "Connection aborted"
CONNECTED_PATTERN = "Client connected: {}:{}"
ERROR_ARGUMENTS = "Provide port number as the first command line argument"
ERROR_OCCURRED = "Error Occurred"
EXIT = "exit"
JOIN_PATTERN = "{username} has joined"
RUNNING = "Server is running..."
SERVER = "SERVER"
SHUTDOWN_MESSAGE = "shutdown"
TYPE_EXIT = "Type 'exit' to exit>"
FIELD_SIZE = 8


class Server(object):
    def __init__(self, argv):
        self.clients = {}
        self.listen_thread = None
        self.port = None
        self.sock = None
        self.game_matrix = None
        self.parse_args(argv)
        self.client_threads = {}

    def listen(self):
        self.sock.listen(1)
        while True:
            try:
                client, address = self.sock.accept()
            except OSError:
                print(CONNECTION_ABORTED)
                return
            wait = threading.Thread(target=self.wait_for_others, args=(client,))
            if len(self.clients) <= 4:
                print(CONNECTED_PATTERN.format(*address))
                self.clients[client] = address[1]
                message = model.Message(message="hello")
                client.sendall(message.marshal())
                wait.start()
            if len(self.clients) == 4:
                wait.join()
                threading.Thread(target=self.handle).start()
                self.sock.close()
                return

    def adding_to_the_game(self, client):
        for i in range(2):
            for j in range(2):
                if self.game_matrix[i * (FIELD_SIZE - 1)][j * (FIELD_SIZE - 1)][0][1] == "none":
                    self.game_matrix[i * (FIELD_SIZE - 1)][j * (FIELD_SIZE - 1)][0][0] = 1
                    self.game_matrix[i * (FIELD_SIZE - 1)][j * (FIELD_SIZE - 1)][0][1] = self.clients[client]
                    return

    def wait_for_others(self, client):
        while True:
            try:
                message = model.Message(**json.loads(self.receive(client)))
            except (ConnectionAbortedError, ConnectionResetError):
                print(CONNECTION_ABORTED)
                return
            if message.quit:
                client.close()
                return
            if message.username:
                if message.username in list(self.clients.values()):
                    client.sendall(model.Message(message="wrong name").marshal())
                    self.clients.pop(client)
                    client.close()
                else:
                    self.clients[client] = message.username
                return

    def check_dead(self, username):
        for i in range(FIELD_SIZE):
            for j in range(FIELD_SIZE):
                for team in self.game_matrix[i][j]:
                    if (team[1] == username):
                        return False
        return True

    def delete_warriors(self, username):
        for i in range(FIELD_SIZE):
            for j in range(FIELD_SIZE):
                for team in self.game_matrix[i][j]:
                    if (team[1] == username):
                        if len(self.game_matrix[i][j]) > 1:
                            self.game_matrix[i][j].remove(team)
                        else:
                            team[0] = 0
                            team[1] = "none"

    def one_round(self, first_round):
        # battles and warriors doubling
        for i in range(FIELD_SIZE):
            for j in range(FIELD_SIZE):
                if len(self.game_matrix[i][j]) > 1:
                    min_warriors = self.game_matrix[i][j][0][0]
                    for team in self.game_matrix[i][j]:
                        if (team[0] < min_warriors):
                            min_warriors = team[0]
                    for team in self.game_matrix[i][j]:
                        team[0] -= min_warriors
                    teams = 0
                    while teams < len(self.game_matrix[i][j]):
                        team = self.game_matrix[i][j][teams]
                        if team[0] == 0:
                            self.game_matrix[i][j].remove(team)
                            teams -= 1
                        teams += 1
                    if (not self.game_matrix[i][j]):
                        self.game_matrix[i][j] = [[0, "none"]]
                elif self.game_matrix[i][j][0][0] > 0:
                    if (not first_round):
                        self.game_matrix[i][j][0][0] = 2 * self.game_matrix[i][j][0][0]

        self.broadcast_game_matrix()

        # check on dead
        keylist = list(self.clients.keys())
        i = 0
        while (i < len(keylist)):
            client = keylist[i]
            if (self.check_dead(self.clients[client])):
                client.sendall(model.Message(message="you lost").marshal())
                client.close()
                self.clients.pop(client)
                keylist = list(self.clients.keys())
                i -= 1
            i += 1

        # check on winning

        if (len(self.clients) == 1):
            return True

        if (len(self.clients) == 0):
            return True

        i = 0
        clients = list(self.clients.keys())
        while len(clients) > i:
            clients = list(self.clients.keys())
            i %= len(clients)
            self.one_turn(clients[i])
            # threading.Thread(target=self.one_turn, args = clients[i]).start()
            i += 1
        return False

    def one_turn(self, client):
        # let client move
        client.sendall(model.Message(message="move").marshal())
        while True:
            try:
                message = model.Message(**json.loads(self.receive(client)))
            except (ConnectionAbortedError, ConnectionResetError):
                print(CONNECTION_ABORTED)
                return
            if message.quit:
                client.sendall(model.Message(message="you lost").marshal())
                client.close()
                self.delete_warriors(self.clients[client])
                self.clients.pop(client)
                return
            elif message.end_turn:
                client.sendall(model.Message(message="wait").marshal())
                return
            else:
                # do player's move
                move = message.message
                # maybe check on cheating but not now
                if move:
                    self.game_matrix = move
                    self.broadcast_game_matrix()

    def handle(self):
        self.temp = True
        for client in self.clients.keys():
            self.adding_to_the_game(client)
        while True:
            if (self.one_round(self.temp)):
                for i in self.clients.keys():
                    i.sendall(model.Message(message="you win").marshal())
                    i.close()
                self.exit()
                return
            self.temp = False

    def broadcast_game_matrix(self):
        message = model.Message(message=self.game_matrix)
        self.broadcast(message)

    def broadcast(self, message):
        for client in self.clients.keys():
            client.sendall(message.marshal())

    def receive(self, client):
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += client.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def run(self):
        print(RUNNING)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("", self.port))
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def parse_args(self, argv):
        if len(argv) != 2:
            raise RuntimeError(ERROR_ARGUMENTS)
        try:
            self.port = int(argv[1])
        except ValueError:
            raise RuntimeError(ERROR_ARGUMENTS)
        self.game_matrix = [[]]
        for i in range(FIELD_SIZE):
            for j in range(FIELD_SIZE):
                self.game_matrix[i].append([[0, "none"]])
            if (i < FIELD_SIZE - 1):
                self.game_matrix.append([])

    def exit(self):
        for client in self.clients.keys():
            client.close()
        print(CLOSING)


if __name__ == "__main__":
    try:
        Server(sys.argv).run()
    except RuntimeError as error:
        print(ERROR_OCCURRED)
        print(str(error))
