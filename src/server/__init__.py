import random
import socket
import threading
from queue import *
import pygame

from server.timer import Timer
from server.word_library import easy_word_set, hard_word_set
from server.words_server import Word
from server.player import Player
from server.functions import get_opponent


lock = threading.Lock()
server_lock = threading.Lock()
server_check = threading.Event()


class Server:
    HEADER = 64
    PORT = 5050
    SERVER = "192.168.1.42"
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
        self.client_threads = {}
        self.game_threads = {}

    """
    Stage 0:
    client data format
      [game_id, client_id, client_game_state, name]
    src data format
      [game_id, game_state, lobby_count]

    Stage 1:
    client data format:
    --
    src data format:
    [game_id, game_state, countdown, opponent_name]

    Stage 2: 
    client data format: 
    [game_id, client_id, client_game_state, word_submit, action_index] 
    src data format: 
    [game_id, game_state, opponent_action_index, ability, debuff, time_seconds : client_id, score | client_id,score : word_id,
    word_code,fall_speed,x_pos,y_pos | word_id,word_code,fall_speed,x_pos,y_pos | , ....] 

    Stage 3:
    client data format:
        [game_id, client_id, client_game_state, play_again] 1 play again 0 not
    src data format:
        [game_id, game_state, : client_id, score, play_again | client_id, score, play_again]
    
    Restart Message:
        [game_id, restart, : client_id, score, play_again | client_id, score, play_again]
    """

    def handle_client(self, conn, addr, client_id, game_id):
        conn.send(str.encode(str(game_id) + "," + str(client_id)))

        print(f"[NEW CONNECTION] {addr} connected")

        current_game = self.games[game_id]
        recv_q = current_game.client_queues[client_id]
        while self.games[game_id].players[client_id].connected:

            data = conn.recv(4096)
            reply = data.decode('utf-8')
            if not data or data == "DISCONNECT":
                conn.sendall(str.encode("Receiving data empty. Disconnecting"))
                print(f'disconnected from {addr} ')
                break
            # print('reply', reply)
            client_data_arr = reply.split(",")
            rcv_game_id = int(client_data_arr[0])
            rcv_id = int(client_data_arr[1])
            rcv_game_state = int(client_data_arr[2])
            if rcv_id != client_id or rcv_game_id != game_id:
                print('token not authorized')
                conn.sendall(str.encode("Token not authorized. Disconnecting"))
                print(f'disconnected from {addr} ')
                break
            # with lock:
                # print(f'client thread {str(client_id)} got a lock')
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
                # print("msg_1", msg)
                conn.sendall(str.encode(msg))
            elif current_game.game_state == 2:
                if rcv_game_state == current_game.game_state:
                    word_submit = str(client_data_arr[3])
                    action_index = int(client_data_arr[4])
                    recv_q.put([client_id, word_submit, action_index])
                msg = str(game_id) + "," + str(current_game.game_state) + "," \
                      + str(current_game.players[get_opponent(client_id)].action_index) \
                      + "," + str(current_game.players[client_id].ability) + "," \
                      + str(current_game.players[client_id].debuff) + "," \
                      + str(current_game.time) + ":" + current_game.frame_string
                current_game.players[client_id].ability = 0
                current_game.players[client_id].debuff = 0
                # print('msg_2', msg)
                conn.sendall(str.encode(msg))
            elif current_game.game_state == 3:
                if rcv_game_state == current_game.game_state:
                    # print('END')
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
                        msg += str(key) + "," + str(current_game.players[key].score) + "," + str(
                            1 if current_game.players[key].play_again else 0) + "|"
                    msg = msg[:-1]
                conn.sendall(str.encode(msg))
            # print(f'client thread {str(client_id)} released a lock')
        conn.sendall(str.encode("DISCONNECT"))

    def run_game_serve(self):
        self.server.listen()
        print(f"[LISTENING] Server is listening on {self.SERVER}")
        client_id = 0
        pygame.init()
        game_id = 0
        # server_manager = threading.Thread(target=self.server_manager)
        # server_manager.start()
        while True:

            conn, addr = self.server.accept()
            curr_key = str(game_id) + str(client_id)
            # with server_lock:
            self.client_threads[curr_key] = threading.Thread(target=self.handle_client, args=(conn, addr, client_id, game_id))
            if client_id == 0:
                self.games[game_id] = Game(game_id, {})
                print('opened room', game_id)
                self.games[game_id].players[client_id] = Player('', client_id, game_id)
                print('Added player', client_id, 'to', 'room', game_id)
                self.games[game_id].client_queues[client_id] = Queue()
                self.game_threads[game_id] = threading.Thread(target=self.games[game_id].run_game_room)
                self.game_threads[game_id].start()
                client_id += 1
            elif client_id == 1:
                self.games[game_id].players[client_id] = Player('', client_id, game_id)
                print('Added player', client_id, 'to', 'room', game_id)
                self.games[game_id].client_queues[client_id] = Queue()
                game_id += 1
                client_id = 0
            self.client_threads[curr_key].start()
            # server_check.set()
            # server_check.clear()
            print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1 - len(self.client_threads)}")

    def server_manager(self):
        while True:
            client_thread_to_remove = []
            server_check.wait()
            with server_lock:
                for key in self.client_threads:
                    if not self.client_threads[key].is_alive():
                        print(f"client thread {key} is DEAD")
                        client_thread_to_remove.append(key)
                        for client_id in self.games[int(key[0])].players:
                            self.games[int(key[0])].players[client_id].connected = False
                        self.games[int(key[0])].stop = True
                for key in client_thread_to_remove:
                    self.client_threads.pop(key)


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
        self.stop = False

    def run_game_room(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            if self.stop:
                break
            while self.game_state == 0:
                if self.stop:
                    break
                all_ready = True
                if len(self.players) == 2:
                    for key in self.players:
                        all_ready = all_ready and self.players[key].ready
                    if all_ready:
                        with lock:
                            # print('game room got a lock')
                            self.game_state = 1
                            # print('game room released a lock')

            start_ticks = pygame.time.get_ticks()
            while self.game_state == 1:
                if self.stop:
                    break
                framerate = clock.tick(30)
                seconds = 10 - int((pygame.time.get_ticks() - start_ticks) / 1000)
                self.countdown = str(seconds)
                if seconds <= 0:
                    with lock:
                        # print('game room got a lock')
                        self.game_state = 2
                        for key in self.players:
                            client_string = str(key) + "," + str(self.players[key].score) + "|"
                            self.frame_string += client_string
                        self.frame_string = self.frame_string[:-1] + ":"
                        # print('game room released a lock')

            word_mem = []

            timer = Timer()
            start_ticks = pygame.time.get_ticks()
            # print('game room got a lock')
            while self.game_state == 2:
                if self.stop:
                    break
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
                        except Empty:
                            pass

                    if len(word_mem) <= 1:
                        timer.tick()
                    if timer.time >= 90:
                        timer.reset()

                    if len(word_mem) <= 1:
                        timer.tick()

                    lottery_num = random.randint(1, 100)

                    if 2 == random.randint(1, 60):
                        if 0 < self.time < 90:
                            if 0 < lottery_num < 80:
                                self.add_easy_word(word_mem)
                            else:
                                self.add_hard_word(word_mem)
                        elif 90 < self.time < 300:
                            if 0 < lottery_num < 80:
                                self.add_hard_word(word_mem)
                            else:
                                self.add_easy_word(word_mem)

                    if len(word_mem) <= 1 and timer.time >= 90:
                        if 0 < self.time < 20:
                            if 0 < lottery_num < 80:
                                self.add_easy_word(word_mem)
                            elif 80 < lottery_num < 100:
                                self.add_hard_word(word_mem)
                        elif 20 < self.time < 300:
                            if 0 < lottery_num < 80:
                                self.add_hard_word(word_mem)
                            elif 80 < lottery_num < 100:
                                self.add_easy_word(word_mem)
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
                                        """
                                        if 7 <= len(word.word) <= 8:
                                            self.players[client_id].ability = 1
                                            self.players[get_opponent(client_id)].debuff = 1
                                        elif 9 <= len(word.word) <= 11:
                                            self.players[client_id].ability = 2
                                            self.players[get_opponent(client_id)].debuff = 2
                                        elif 12 <= len(word.word) <= 13:
                                            self.players[client_id].ability = 3
                                            self.players[get_opponent(client_id)].debuff = 3
                                        elif len(word.word) > 13:
                                            self.players[client_id].ability = 1
                                            self.players[get_opponent(client_id)].debuff = 1
                                        self.players[client_id].score += 1
                                        """
                                        if len(word.word) >= 7:
                                            bamboozle = random.randint(1, 3)
                                            self.players[client_id].ability = bamboozle
                                            self.players[get_opponent(client_id)].debuff = bamboozle
                                        self.players[client_id].score += 1
                                        # print('plus')
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
                if self.stop:
                    break
                framerate = clock.tick(30)
                for key in self.client_queues:
                    try:
                        x = self.client_queues[key].get_nowait()
                        self.sync_data(x)
                    except Empty:
                        pass
                self.play_again = True
                for key in self.players:
                    self.play_again = self.play_again and self.players[key].play_again
                if self.play_again:
                    # print('game room got a lock')
                    self.game_state = 1
                    self.reset_data()
                    # print('game room released a lock')

    @staticmethod
    def move_word(w):
        w.text_rect.move_ip(0, w.fall_speed)

    def add_easy_word(self, word_mem):
        key = random.choice(list(easy_word_set.keys()))
        word_mem.append(Word(self.word_count, key))
        self.word_count += 1
        return easy_word_set[key]

    def stop_thread(self):
        self.stop = True

    def add_hard_word(self, word_mem):
        key = random.choice(list(hard_word_set.keys()))
        word_mem.append(Word(self.word_count, key))
        self.word_count += 1
        return hard_word_set[key]

    def reset_data(self):
        for key in self.players:
            self.players[key].score = 0
            self.players[key].word_submit = ''
            self.players[key].action_index = 0
            self.players[key].ready = False
            self.players[key].play_again = False
            with self.client_queues[key].mutex:
                self.client_queues[key].queue.clear()
        self.play_again = False
        self.time = 0
        self.word_count = 0
        self.frame_string = ''

    def sync_data(self, client_input):
        if self.game_state == 0:
            self.players[client_input[0]].name = client_input[1]
            # print('client input', client_input)
        if self.game_state == 2:
            self.players[client_input[0]].word_submit = client_input[1]
            self.players[client_input[0]].action_index = client_input[2]
        elif self.game_state == 3:
            if client_input[1] != ' ':
                self.players[client_input[0]].play_again = int(client_input[1])
