import re
from queue import *

import pygame

from network import *
from player import Player
from timer import Timer
from words_client import Word


class Game:

    def __init__(self):
        pygame.init()
        self.net = Network()
        self.width = 1024
        self.height = 720
        self.font = pygame.font.Font('freesansbold.ttf', 32)
        self.player_me = Player('Mon', self.net.id)
        self.player_dict = {self.player_me.id: self.player_me}
        self.submit_queue = Queue()
        self.status = 0
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('client1')
        self.current_frame_string = ''
        self.word_mem = {}
        self.clock = pygame.time.Clock()
        self.game_state = 0

    def wait_conn(self):
        pass

    def wait_reply(self):
        pass

    def run_lobby(self):
        while self.game_state == 0:
            framerate = self.clock.tick(30)
            data = self.send_data('').split(',') #recv data from server
            self.game_state = int(data[0])
            self.screen.fill(pygame.Color('white'))
            self.draw_Enter_Name()
            self.draw_Input_Name()
            #self.draw_connected_player_count(data[1])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            pygame.display.update()

        self.count_down()

    def count_down(self):
        while self.game_state == 1:
            framerate = self.clock.tick(30)
            data = self.send_data('').split(',')
            self.game_state = int(data[0])
            self.screen.fill(pygame.Color('white'))
            self.draw_countdown_timer(data[1])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            pygame.display.update()

        self.start_game()

    def start_game(self):

        running = True
        backspace_clock = Timer()

        while running:
            framerate = self.clock.tick(30)
            backspace_clock.tick()
            keys = pygame.key.get_pressed()

            player_dict, word_dict = self.parse_data(self.current_frame_string)
            self.sync_data(player_dict, word_dict)

            if keys[pygame.K_BACKSPACE] and len(self.player_me.keystrokes) > 0 and backspace_clock.time >= 2:
                backspace_clock.reset()
                self.player_me.keystrokes = self.player_me.keystrokes[:-1]
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.unicode.isalpha() or event.unicode == '-':
                        self.player_me.keystrokes += event.unicode
                    elif event.unicode == '\r':
                        self.player_me.confirm_key = True

            self.screen.fill(pygame.Color('white'))
            self.draw_score(self.player_me.score)
            self.draw_current_stroke(self.player_me.keystrokes)

            for word_id in self.word_mem:
                if self.player_me.keystrokes == '':
                    s = False
                else:
                    s = re.search("^" + self.player_me.keystrokes, self.word_mem[word_id].word)  #match the start of the string
                if s:
                    self.word_mem[word_id].match_text(s.span())
                    self.word_mem[word_id].start_match = True
                    self.print_move_word(self.word_mem[word_id])
                    self.print_move_matching_word(self.word_mem[word_id])
                elif self.word_mem[word_id].start_match:
                    self.word_mem[word_id].start_match = False
                    self.word_mem[word_id].unmatch_text()
                    self.print_move_word(self.word_mem[word_id])
                else:
                    print('print word')
                    self.print_move_word(self.word_mem[word_id])

            print(self.current_frame_string)
            if self.player_me.confirm_key:
                self.current_frame_string = self.send_data(self.player_me.keystrokes)
                self.player_me.keystrokes = ''
                self.player_me.confirm_key = False
            else:
                self.current_frame_string = self.send_data('')
            pygame.display.update()

    def send_data(self, key_strokes):    #compute clientdata to send form client to server
        if key_strokes != '':
            data = str(self.net.id) + "," + str(self.status) + "," + str(key_strokes)
        else:
            data = str(self.net.id) + "," + str(self.status) + "," + str(' ')
        reply = self.net.send(data)
        return reply

    @staticmethod
    def parse_data(data):
        try:
            player_data, word_data = data.split(":")[0], data.split(":")[1]
            player_list = player_data.split("|")
            word_list = word_data.split("|")
            player_dict = {}
            word_dict = {}
            for player_string in player_list:
                player = player_string.split(",")
                player_dict[player[0]] = player[1:]
            for word_string in word_list:
                word_separated_data = word_string.split(",")
                word_dict[word_separated_data[0]] = word_separated_data
            return player_dict, word_dict
        except:
            return {}, {}

    def sync_data(self, player_data_dict, word_data_dict):
        for player_id in player_data_dict:
            if player_id not in self.player_dict:
                self.player_dict[player_id] = Player('player2', player_id)
            else:
                self.player_dict[player_id].score = player_data_dict[player_id][0]
        for word_data in word_data_dict:
            if word_data in self.word_mem:
                self.word_mem[word_data].x_pos = x = int(word_data_dict[word_data][3])
                self.word_mem[word_data].y_pos = y = int(word_data_dict[word_data][4])
                self.word_mem[word_data].text_rect.topleft = (x, y)
            else:
                self.word_mem[word_data] = Word(int(word_data_dict[word_data][0]), int(word_data_dict[word_data][1]),
                                                int(word_data_dict[word_data][2]), int(word_data_dict[word_data][3]),
                                                int(word_data_dict[word_data][4]))

        keys_to_keep = set(word_data_dict.keys()).intersection(set(self.word_mem.keys()))
        self.word_mem = {k: v for k, v in self.word_mem.items() if k in keys_to_keep}


    def get_Name(self):
        self.name = pygame.key.name()

    def draw_Enter_Name(self):
        Enter_text = self.font.render('Enter Your Name :', True, pygame.Color('black'))
        Enter_text_rect = Enter_text.get_rect()
        Enter_text_rect.topright = (512, 320)
        self.screen.blit(Enter_text, Enter_text_rect)

    def draw_Input_Name(self, name):
        Name_text = self.font.render(str(name), True, pygame.Color('black'))
        Name_text_rect = Name_text.get_rect()
        Name_text_rect.topleft = (512, 320)
        self.screen.blit(Name_text, Name_text_rect)

    def draw_score(self, score):
        score_text = self.font.render('score:' + str(score), True, pygame.Color('black'))
        score_text_rect = score_text.get_rect()
        score_text_rect.topleft = (0, 0)
        self.screen.blit(score_text, score_text_rect)

    def draw_current_stroke(self, current_stroke):
        score_text = self.font.render(current_stroke, True, pygame.Color('black'))
        score_text_rect = score_text.get_rect()
        score_text_rect.midbottom = (512, 710)
        self.screen.blit(score_text, score_text_rect)

    def draw_connected_player_count(self, player_count):
        font = pygame.font.Font('freesansbold.ttf', 50)
        text = font.render('Connected Players:' + str(player_count) + '/2', True, pygame.Color('black'))
        text_rect = text.get_rect()
        text_rect.center = (int(self.width / 2), int(self.height / 2))
        self.screen.blit(text, text_rect)

    def draw_countdown_timer(self, time):
        font = pygame.font.Font('freesansbold.ttf', 50)
        text = font.render('Game Starting In:' + time, True, pygame.Color('black'))
        text_rect = text.get_rect()
        text_rect.center = (int(self.width / 2), int(self.height / 2))
        self.screen.blit(text, text_rect)

    def print_move_word(self, w):
        self.screen.blit(w.text, w.text_rect)
        # w.text_rect.move_ip(0, w.fall_speed)

    def print_move_matching_word(self, w):
        self.screen.blit(w.matching_text, w.matching_text_rect)
        # w.matching_text_rect.move_ip(0, w.fall_speed)


game = Game()
game.run_lobby()
