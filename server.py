import random
import socket
import threading
import time
from queue import *

import pygame

from timer import Timer
from word_library import word_set
from words_server import Word

lock = threading.Lock()

class Player:
    def __init__(self, name, player_id, game_id):
        self.name = name
        self.score = 0
        self.word_submit = ''
        self.status = 0
        self.id = player_id
        self.game_id = game_id
        self.action_index = 0
        self.ready = False
        self.play_again = False


class Server:
    HEADER = 64
    PORT = 5050
    SERVER = "192.168.1.11"
    ADDR = (SERVER, PORT)
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind(self.ADDR)
        except socket.error as e:
            print('error', str(e))
        self.games = {}


    """
    Stage 0:
    client data format
      [game_id, client_id, client_game_state, name]
    server data format
      [game_id, game_state, lobby_count]

    Stage 1:
    client data format:
    --
    server data format:
    [game_id, game_state, countdown, opponent_name]

    Stage 2: 
    client data format: 
    [game_id, client_id, client_game_state, word_submit, action_index] 
    server data format: 
    [game_id, game_state, opponent_action_index, time_seconds : client_id, score | client_id,score : word_id,
    word_code,fall_speed,x_pos,y_pos | word_id,word_code,fall_speed,x_pos,y_pos | , ....] 
    
    index = 0 ; no thing happens
    index = 1 ; 
    index = 2 ;

    Stage 3:
    client data format:
        [game_id, client_id, client_game_state, play_again] 1 play again 0 not
    server data format:
        [game_id, game_state, : client_id, score, play_again | client_id, score, play_again]
    
    Restart Message:
        [game_id, restart, : client_id, score, play_again | client_id, score, play_again]
    """

    def handle_client(self, conn, addr, client_id, game_id):
        conn.send(str.encode(str(game_id) + "," + str(client_id)))

        print(f"[NEW CONNECTION] {addr} connected")

        connected = True
        current_game = self.games[game_id]
        recv_q = current_game.client_queues[client_id]
        while connected:

            data = conn.recv(4096)
            reply = data.decode('utf-8')
            if not data or data == "DISCONNECT":
                conn.sendall(str.encode("Receiving data empty. Disconnecting"))
                print(f'disconnected from {addr} ')
                break
            print('reply', reply)
            client_data_arr = reply.split(",")
            rcv_game_id = int(client_data_arr[0])
            rcv_id = int(client_data_arr[1])
            rcv_game_state = int(client_data_arr[2])
            if rcv_id != client_id or rcv_game_id != game_id:
                print('token not authorized')
                conn.sendall(str.encode("Token not authorized. Disconnecting"))
                print(f'disconnected from {addr} ')
                break
            with lock:
                print(f'client thread {str(client_id)} got a lock')
                if current_game.game_state == 0:
                    if rcv_game_state == current_game.game_state:
                        name = str(client_data_arr[3])
                        if name != "" or " ":
                            current_game.players[client_id].ready = True
                        current_game.sync_data([client_id, name])
                    msg = str(game_id) + "," + str(current_game.game_state) + "," + str(len(current_game.players))
                    # print(msg)
                    # print("msg_0", msg)
                    conn.sendall(str.encode(msg))
                elif current_game.game_state == 1:
                    msg = str(game_id) + "," + str(current_game.game_state) + "," + current_game.countdown + "," + \
                          current_game.players[
                              get_opponent(client_id)].name
                    print("msg_1", msg)
                    conn.sendall(str.encode(msg))
                elif current_game.game_state == 2:
                    if rcv_game_state == current_game.game_state:
                        word_submit = str(client_data_arr[3])
                        action_index = int(client_data_arr[4])
                        recv_q.put([client_id, word_submit, action_index])
                    msg = str(game_id) + "," + str(current_game.game_state) + "," + str(current_game.players[get_opponent(client_id)].action_index) + "," + str(current_game.time) + ":" + current_game.frame_string
                    print('msg_2', msg)
                    conn.sendall(str.encode(msg))
                elif current_game.game_state == 3:
                    if rcv_game_state == current_game.game_state:
                        print('END')
                        play_again = True if int(client_data_arr[3]) == 1 else False
                        recv_q.put([client_id, play_again])
                    if current_game.play_again:
                        msg = str(game_id) + "," + "restart" + ":"
                        for key in current_game.players:
                            msg += str(key) + "," + str(current_game.players[key].score) + "," + str(
                                1 if current_game.players[key].play_again else 0) + "|"
                        msg = msg[:-1]
                    else:
                        msg = str(game_id) + "," + str(current_game.game_state) + ":"
                        for key in current_game.players:
                            msg += str(key) + "," + str(current_game.players[key].score) + "," + str(1 if current_game.players[key].play_again else 0) + "|"
                        msg = msg[:-1]
                    conn.sendall(str.encode(msg))
            print(f'client thread {str(client_id)} released a lock')

    def run_game_serve(self):
        self.server.listen()
        print(f"[LISTENING] Server is listening on {self.SERVER}")
        client_id = 0
        pygame.init()
        game_id = 0
        while True:
            conn, addr = self.server.accept()
            thread_client = threading.Thread(target=self.handle_client,
                                             args=(conn, addr, client_id, game_id))
            if client_id == 0:
                self.games[game_id] = Game(game_id, {})
                print('opened room', game_id)
                self.games[game_id].players[client_id] = Player('', client_id, game_id)
                print('Added player', client_id, 'to', 'room', game_id)
                self.games[game_id].client_queues[client_id] = Queue()
                thread_game = threading.Thread(target=self.games[game_id].run_game_room)
                thread_game.start()
                client_id += 1
            elif client_id == 1:
                self.games[game_id].players[client_id] = Player('', client_id, game_id)
                print('Added player', client_id, 'to', 'room', game_id)
                self.games[game_id].client_queues[client_id] = Queue()
                game_id += 1
                client_id = 0
            thread_client.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1 - len(self.games)}")


class Game:
    def __init__(self, game_id, players):
        self.game_id = game_id
        self.game_state = 0
        self.frame_string = ''
        self.word_count = 0
        self.countdown = ''
        self.players = players
        self.time = 0
        self.client_queues = {}
        self.play_again = False

    def run_game_room(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            while self.game_state == 0:
                all_ready = True
                if len(self.players) == 2:
                    for key in self.players:
                        all_ready = all_ready and self.players[key].ready
                    if all_ready:
                        with lock:
                            print('game room got a lock')
                            self.game_state = 1
                            print('game room released a lock')

            start_ticks = pygame.time.get_ticks()
            while self.game_state == 1:
                framerate = clock.tick(30)
                seconds = 10 - int((pygame.time.get_ticks() - start_ticks) / 1000)
                self.countdown = str(seconds)
                if seconds <= 0:
                    with lock:
                        print('game room got a lock')
                        self.game_state = 2
                        for key in self.players:
                            client_string = str(key) + "," + str(self.players[key].score) + "|"
                            self.frame_string += client_string
                        self.frame_string = self.frame_string[:-1] + ":"
                        print('game room released a lock')

            word_mem = []

            timer = Timer()
            start_ticks = pygame.time.get_ticks()
            print('game room got a lock')
            while self.game_state == 2:
                framerate = clock.tick(30)
                with lock:
                    self.time = int((pygame.time.get_ticks() - start_ticks) / 1000)
                    if self.time == 300:
                        self.game_state = 3
                    frame_string = ""
                    for key in self.client_queues:
                        try:
                            x = self.client_queues[key].get_nowait()
                            self.sync_data(x)
                        except Empty as e:
                            pass

                    if len(word_mem) <= 1:
                        timer.tick()
                    if timer.time >= 90:
                        timer.reset()

                    if len(word_mem) <= 1:
                        timer.tick()
                    if 2 == random.randint(1, 60):
                        self.add_new_word(word_mem)
                    if len(word_mem) <= 1 and timer.time >= 90:
                        self.add_new_word(word_mem)
                        timer.reset()

                    removed_words = []

                    for word in word_mem:
                        if not word.disabled:
                            self.move_word(word)
                            if word.text_rect.bottomleft[1] > 730:
                                word.disable()
                                removed_words.append(word)

                            for client_id in self.players:
                                if self.players[client_id].word_submit != " ":
                                    if (self.players[client_id].word_submit == word.word) and (not word.disabled):
                                        self.players[client_id].score += 1
                                        print('plus')
                                        word.disable()
                                        removed_words.append(word)
                                    else:
                                        print(self.players[client_id].word_submit + "!=" + word.word)
                        else:
                            removed_words.append(word)

                    for client_id in self.players:
                        self.players[client_id].word_submit = " "

                    if len(removed_words) > 0:
                        word_mem = [i for i in word_mem if i not in removed_words]
                    for key in self.players:
                        client_string = str(key) + "," + str(self.players[key].score) + "|"
                        frame_string += client_string
                    frame_string = frame_string[:-1] + ":"
                    for word in word_mem:
                        word_string = str(word.id) + "," + str(word.word_code) + "," + str(word.fall_speed) + "," + str(
                            word.text_rect.topleft[0]) + "," + str(word.text_rect.topleft[1]) + "|"
                        frame_string += word_string
                    self.frame_string = frame_string[:-1]

            while self.game_state == 3:
                framerate = clock.tick(30)
                for key in self.client_queues:
                    try:
                        x = self.client_queues[key].get_nowait()
                        self.sync_data(x)
                    except Empty as e:
                        pass
                self.play_again = True
                for key in self.players:
                    self.play_again = self.play_again and self.players[key].play_again
                if self.play_again:
                    print('game room got a lock')
                    self.game_state = 1
                    self.reset_data()
                    print('game room released a lock')


        while self.game_state == 3:
            for key in self.client_queues:
                try:
                    x = self.client_queues[key].get_nowait()
                    self.sync_data(x)
                    print(x)
                except Empty as e:
                    pass
            play_again = False
            for key in self.players:
                play_again = play_again and self.players[key].play_again
            if play_again:
                self.game_state == 2




    @staticmethod
    def move_word(w):
        w.text_rect.move_ip(0, w.fall_speed)

    def add_new_word(self, word_mem):
        key = random.choice(list(word_set.keys()))
        word_mem.append(Word(self.word_count, key))
        self.word_count += 1
        return word_set[key]

    @staticmethod
    def parse_data(self, data):
        pass

    def reset_data(self):
        for key in self.players:
            self.players[key].score = 0
            self.players[key].word_submit = ''
            self.players[key].action_index = 0
            self.players[key].ready = False
            self.players[key].play_again = False
        self.play_again = False
        self.time = 0
        self.word_count = 0
        self.frame_string = ''

    def sync_data(self, client_input):
        if self.game_state == 0:
            self.players[client_input[0]].name = client_input[1]
            print('client input', client_input)
        if self.game_state == 2:
            self.players[client_input[0]].word_submit = client_input[1]
            self.players[client_input[0]].action_index = client_input[2]
        elif self.game_state == 3:
            if client_input[1] != ' ':
                self.players[client_input[0]].play_again = int(client_input[1])


def get_opponent(self_id):
    if self_id == 1:
        return 0
    elif self_id == 0:
        return 1
    else:
        return 'error'


if __name__ == "__main__":
    server = Server()
    server.run_game_serve()