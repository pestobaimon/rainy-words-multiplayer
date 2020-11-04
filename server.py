import random
import socket
import threading
from queue import *

import pygame

from timer import Timer
from word_library import word_set
from words_server import Word

thread_event = threading.Event()


class Player:
    def __init__(self, name, player_id):
        self.name = name
        self.score = 0
        self.word_submit = ''
        self.status = 0
        self.id = player_id


class Server:
    HEADER = 64
    PORT = 5050
    SERVER = "100.67.128.104"
    ADDR = (SERVER, PORT)
    FORMAT = 'utf-8'
    DISCONNECT_MESSAGE = "!DISCONNECT"

    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind(self.ADDR)
        except socket.error as e:
            print(str(e))
        self.frame_data = []
        self.players = {}
        self.frame_string = ''
        self.client_queues = {}
        self.word_count = 0
        self.game_state = 0
        self.countdown = ''

    """
    frameData format
      client_id,score | client_id,score : word_id,word_code,fall_speed,x_pos,y_pos | word_id,word_code,fall_speed,x_pos,y_pos | ,....
    clientData format
      [client_id, status, word_submit]
    
    """

    def handle_client(self, conn, addr, client_id, recv_q, clock):
        conn.send(str.encode(str(client_id)))

        print(f"[NEW CONNECTION] {addr} connected")

        connected = True

        while connected:
            try:
                data = conn.recv(4096)
                reply = data.decode('utf-8')
                if not data:
                    conn.send(str.encode("Receiving data empty. Disconnecting"))
                    break
                else:
                    client_data_arr = reply.split(",")
                    rcv_id = int(client_data_arr[0])
                    status = int(client_data_arr[1])
                    word_submit = str(client_data_arr[2])
                    if rcv_id != client_id:
                        connected = False
                        print('token not authorized')
                    elif word_submit == ' ':
                        pass
                    else:
                        recv_q.put([rcv_id, status, word_submit])
                if self.game_state == 0:
                    print('LOBBY')
                    lobby_count = threading.activeCount() - 1
                    msg = "0" + "," + str(lobby_count)
                    conn.sendall(str.encode(msg))
                elif self.game_state == 1:
                    print('COUNTDOWN')
                    msg = "1" + "," + self.countdown
                    thread_event.wait()
                    conn.sendall(str.encode(msg))
                elif self.game_state == 2:
                    thread_event.wait()
                    conn.sendall(str.encode(self.frame_string))
            except:
                break

    def start(self):
        self.server.listen()
        print(f"[LISTENING] Server is listening on {self.SERVER}")
        lobby_full = False
        client_id = 0
        pygame.init()
        clock = pygame.time.Clock()

        while self.game_state == 0:
            conn, addr = self.server.accept()
            self.client_queues[client_id] = Queue()
            self.players[client_id] = Player(str(client_id), client_id)
            thread = threading.Thread(target=self.handle_client,
                                      args=(conn, addr, client_id, self.client_queues[client_id], clock))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")
            client_id += 1
            if threading.activeCount() - 1 == 2:
                self.game_state = 1

        start_ticks = pygame.time.get_ticks()
        while self.game_state == 1:
            framerate = clock.tick(30)
            seconds = int((pygame.time.get_ticks() - start_ticks) / 1000)
            if seconds == 0:
                self.countdown = "3"
            elif seconds == 1:
                self.countdown = "2"
            elif seconds == 2:
                self.countdown = "1"
            else:
                self.game_state = 2
            thread_event.set()
            thread_event.clear()

        word_mem = []

        timer = Timer()
        while self.game_state == 2:
            framerate = clock.tick(30)
            self.frame_string = ""
            for key in self.client_queues:
                try:
                    x = self.client_queues[key].get_nowait()
                    self.sync_data(x)
                    print(x)
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
                    if word.text_rect.bottomleft[1] > 800:
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
                self.frame_string += client_string
            self.frame_string = self.frame_string[:-1] + ":"
            for word in word_mem:
                word_string = str(word.id) + "," + str(word.word_code) + "," + str(word.fall_speed) + "," + str(
                    word.text_rect.topleft[0]) + "," + str(word.text_rect.topleft[1]) + "|"
                self.frame_string += word_string
            self.frame_string = self.frame_string[:-1]
            # print(self.frame_string)
            thread_event.set()
            thread_event.clear()

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

    def sync_data(self, client_input):
        self.players[client_input[0]].status = client_input[1]
        self.players[client_input[0]].word_submit = client_input[2]


server = Server()
server.start()
