import re
from queue import *
from network import *
from player import Player
from timer import Timer
from words_client import Word
from png_sprite import *
import pygame
from pygame import mixer


class Game:

    def __init__(self):

        # game user
        pygame.init()
        self.net = Network()
        self.player_me = Player('Player 1', self.net.id)
        self.player_friend = Player('Player 2', '1' if self.net.id == '0' else '0')
        self.player_dict = {self.player_me.id: self.player_me, self.player_friend.id: self.player_friend}

        # game interface
        self.width = 1024
        self.height = 720
        self.font = pygame.font.Font('Assets/font/pixelmix.ttf', 32)
        self.player_bongo_me = bongo_sprite
        self.player_bongo_friend = bongo_sprite
        self.player_x_me = 50
        self.player_y_me = 420
        self.player_x_friend = 670
        self.player_y_friend = 420
        # display client -> server
        self.draw_state_me = 0
        self.draw_state_friend = 0

        # display client
        self.draw_index = 0
        self.vfx_boom = boom_sprite
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.flip_screen = pygame.display.set_mode((self.width, self.height))
        self.keys_to_play = []
        self.word_to_play_mem = []
        pygame.display.set_caption('client1')

        # game system
        self.submit_queue = Queue()
        self.status = 0
        self.current_frame_string = ''
        self.word_mem = {}
        self.clock = pygame.time.Clock()
        self.game_state = 0
        self.game_id = ''
        self.game_time = 0
        self.count_down_time = '0'
        self.play_again_me = 0
        self.removed_word_animation = []
        self.backspace_clock = Timer()
        self.type_state = False
        self.mouse_pos = []
        self.lobby_count = 0
        self.msg = ''

        # game soundtrack
        mixer.music.load('Assets/sound/NESNyan.mp3')
        mixer.music.set_volume(0.05)
        mixer.music.play(-1)

        # game sfx
        self.explo_sound = mixer.Sound('Assets/sound/8bitexplo.mp3')
        self.explo_sound.set_volume(0.5)
        self.meow_sound = mixer.Sound('Assets/sound/meow.mp3')
        self.meow_sound.set_volume(0.5)
        self.cd_sound = mixer.Sound('Assets/sound/MarioKCD.mp3')
        self.cd_sound.set_volume(0.1)

    def start(self):
        playing = True
        self.insert_name()
        self.current_frame_string = self.send_data(self.player_me.name)
        while playing:
            framerate = self.clock.tick(30)
            game_data_list, player_dict, word_dict = self.parse_data(self.current_frame_string)
            print('current frame string', self.current_frame_string)
            self.sync_data(game_data_list, player_dict, word_dict)
            self.run_lobby()  # gamestate 0
            self.count_down()  # gamestate 1
            self.start_game()  # gamestate 2
            self.result()  # gamestate 3
            print('play again', self.play_again_me)
            self.current_frame_string = self.send_data(self.msg)

    def insert_name(self):
        self.backspace_clock = Timer()
        running = True
        # draw_text(self, text, xpos, ypos, font_size, r, g, b):
        while running:
            framerate = self.clock.tick(30)
            self.mouse_pos = pygame.mouse.get_pos()
            self.backspace_clock.tick()
            keys = pygame.key.get_pressed()
            self.screen.fill(pygame.Color('white'))
            self.screen.blit(pygame.transform.scale(bg_sprite[3], (self.width, self.height)), (0, 0))
            if keys[pygame.K_BACKSPACE] and len(
                    self.player_me.keystrokes) > 0 and self.backspace_clock.time >= 2 and self.type_state:
                self.backspace_clock.reset()
                self.player_me.keystrokes = self.player_me.keystrokes[:-1]
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if 230 <= self.mouse_pos[0] <= 830 and 250 <= self.mouse_pos[1] <= 325:  # text button
                        print('text button clicked!')
                        self.type_state = True
                    elif 410 <= self.mouse_pos[0] <= 610 and 350 <= self.mouse_pos[1] <= 400:
                        if self.type_state and len(self.player_me.keystrokes) > 0:
                            print('confirm button clicked!')
                            self.player_me.name = self.player_me.keystrokes
                            print('Meow ' + self.player_me.name + ' has joined the fray!')
                            self.meow_sound.play()
                            self.player_me.keystrokes = ''
                            running = False
                        else:
                            print('hey what is your name?')
                    else:
                        self.type_state = False
                if event.type == pygame.KEYDOWN:
                    if self.type_state:
                        if len(self.player_me.keystrokes) == 20:
                            pass
                        else:
                            self.player_me.keystrokes += event.unicode
            self.draw_text('Please insert your name', 550, 200, 40, 0, 0, 0)
            pygame.draw.rect(self.screen, (255, 255, 255), (410, 350, 200, 50))  # confirm button
            self.screen.blit(pygame.transform.scale(button_sprite[0], (600, 75)), (230, 250))  # text button texture
            self.draw_text('confirm', 510, 370, 30, 0, 0, 0)
            self.draw_name_stroke(self.player_me.keystrokes)
            pygame.display.update()

    def run_lobby(self):
        if self.game_state == 0:
            self.msg = self.player_me.name
            self.screen.fill(pygame.Color('white'))
            self.screen.blit(pygame.transform.scale(bg_sprite[5], (self.width, self.height)), (0, 0))
            self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bg_sprite[4], (750, 400)), 0), (40, 50))
            self.draw_text_waiting('Hello ! , ' + self.player_me.name, 100, 120)
            self.draw_text_waiting('Joined Room ' + str(self.game_id), 100, 180)
            self.draw_text_waiting('Waiting for more bongo...', 85, 240)
            self.draw_connected_player_count(self.lobby_count)
            self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 12.5),
                             (120, 40))
            self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bg_sprite[6], (300, 300)), -12.5),
                             (600, 300))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            pygame.display.update()

    def count_down(self):
        if self.game_state == 1:
            self.play_again_me = 0
            self.screen.fill(pygame.Color('white'))
            self.screen.blit(pygame.transform.scale(bg_sprite[2], (self.width, self.height)), (0, 0))
            if 5 < int(self.count_down_time) <= 10:
                self.draw_text('ARE YOU READY?', 510, 198, 60, 255, 255, 255)
                self.draw_text('ARE YOU READY?', 512, 200, 60, 0, 0, 0)
                if 7 < int(self.count_down_time) <= 8:
                    self.draw_text('Your Opponent is....', 512, 300, 50, 0, 0, 0)
                if 5 < int(self.count_down_time) <= 7:
                    self.draw_text('Your Opponent is....', 512, 300, 50, 0, 0, 0)
                    self.draw_text('Meow ' + self.player_friend.name + '!', 510, 398, 70, 255, 255, 255)
                    self.draw_text('Meow ' + self.player_friend.name + '!', 512, 400, 70, 0, 0, 0)
                    self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[11], (1024, 420)), 0),
                                     (0, 375))
            if 4 <= int(self.count_down_time) <= 5:
                if self.count_down_time == '5':
                    self.draw_text('GAME', 506, 354, 70, 255, 255, 255)
                    self.draw_text('GAME', 512, 360, 70, 0, 0, 0)
                if self.count_down_time == '4':
                    self.draw_text('START!', 506, 354, 70, 255, 255, 255)
                    self.draw_text('START!', 512, 360, 70, 0, 0, 0)
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[12], (1024, 1024)), 12.5),
                                 (-40, 40))
            if self.count_down_time == '3':
                self.cd_sound.play()
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 12.5),
                                 (-40, 40))
                self.draw_countdown_timer(self.count_down_time)
            if self.count_down_time == '2':
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 12.5),
                                 (-40, 40))  # mid bottom
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 192.5),
                                 (-110, -550))  # mid top
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 105),
                                 (350, -300))  # right
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), -80),
                                 (-550, -180))  # left
                self.draw_countdown_timer(self.count_down_time)
            if self.count_down_time == '1':
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 12.5),
                                 (-40, 40))  # mid bottom
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 192.5),
                                 (-110, -550))  # mid top
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 105),
                                 (350, -300))  # right
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), -80),
                                 (-550, -180))  # left
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), -4),
                                 (-390, 125))  # bottom left
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 35.5),
                                 (240, -70))  # bottom right
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 176),
                                 (350, -500))  # top right
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[1], (1024, 1024)), 205.5),
                                 (-620, -610))  # top left
                self.draw_countdown_timer(self.count_down_time)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            self.msg = ''
            pygame.display.update()

    def start_game(self):
        if self.game_state == 2:
            self.backspace_clock.tick()
            keys = pygame.key.get_pressed()
            # redraw per frame
            self.draw_state_me = 0
            self.screen.fill(pygame.Color('white'))
            self.screen.blit(pygame.transform.scale(bg_sprite[0], (self.width, self.height)), (0, 0))
            self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bg_sprite[1], (200, 100)), 2), (70, 570))
            self.screen.blit(
                pygame.transform.flip(pygame.transform.rotate(pygame.transform.scale(bg_sprite[1], (200, 100)), 2),
                                      True, False), (750, 570))

            if keys[pygame.K_BACKSPACE] and len(self.player_me.keystrokes) > 0 and self.backspace_clock.time >= 2:
                self.backspace_clock.reset()
                self.player_me.keystrokes = self.player_me.keystrokes[:-1]
            for event in pygame.event.get():
                self.bongo_animation(self.player_bongo_me, event)
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.unicode.isalpha() or event.unicode == '-':
                        self.player_me.keystrokes += event.unicode
                    elif event.unicode == '\r' or event.key == pygame.K_RETURN:
                        self.player_me.confirm_key = True
            if self.draw_state_me == 2 or self.draw_state_friend == 2:
                self.meow_sound.play()
            if self.draw_state_me == 0:
                self.draw_bongo_cat(self.player_bongo_me[0], 0)

            self.draw_bongo_cat(self.player_bongo_friend[self.draw_state_friend], 1)
            self.screen.blit(pygame.transform.rotate(pygame.transform.scale(addi_sprite[0], (100, 75)), -1), (180, 485))
            self.screen.blit(pygame.transform.rotate(pygame.transform.scale(addi_sprite[1], (110, 80)), 23), (744, 470))
            self.draw_name_me()
            self.draw_score_me(self.player_me.score)
            self.draw_name_friend()
            self.draw_score_friend(self.player_friend.score)
            self.draw_current_stroke(self.player_me.keystrokes)
            self.draw_text(300-self.game_time, 510, 18, 50, 255, 255, 255)
            self.draw_text(300-self.game_time, 512, 20, 50, 0, 0, 0)  # 300 --> total game time

            for word_id in self.word_mem:
                if self.player_me.keystrokes == '':
                    s = False
                else:
                    s = re.search("^" + self.player_me.keystrokes, self.word_mem[word_id].word)
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
                    self.print_move_word(self.word_mem[word_id])
            for word in self.word_to_play_mem:
                word_removed = [self.word_to_play_mem[word], 0]
                self.removed_word_animation.append(word_removed)
            for word in self.removed_word_animation:
                self.display_VFX(word[0], word[1])
                if word[1] == 11:
                    word[1] = 0
                    self.removed_word_animation.remove(word)
                word[1] += 1
            if self.player_me.confirm_key:
                self.msg = self.player_me.keystrokes + "," + str(self.draw_state_me)
                self.player_me.keystrokes = ''
                self.player_me.confirm_key = False
            else:
                self.msg = " ," + str(self.draw_state_me)
            pygame.display.update()

    def result(self):
        if self.game_state == 3:
            self.msg = str(self.play_again_me)
            score_me = self.player_me.score  # A is me
            score_friend = self.player_friend.score  # B is friend
            mouse_pos1 = pygame.mouse.get_pos()  # get tuple (x,y) want x ---> mouse_pos[0]
            if score_me < score_friend:
                self.screen.fill(pygame.Color('white'))
                self.screen.blit(pygame.transform.scale(bg_sprite[7], (self.width, self.height)), (0, 0))
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bg_sprite[8], (600, 200)), 0),
                                 (200, 50))
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[9], (400, 180)), 0),
                                 (300, 550))
                self.draw_text('YOU LOSE', 512, 150, 50, 255, 255, 255)
                self.draw_text('SCORE ' + str(self.player_me.score), 512, 300, 50, 255, 255, 255)
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(button_sprite[1], (280, 98)), 0),
                                 (190, 400))
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(button_sprite[2], (350, 130)), 0),
                                 (530, 390))

                for event in pygame.event.get():  # ดูว่าเกิด event อะไรขึ้น
                    if event.type == pygame.QUIT:  # type คือการกดคีย์บอร์ด #quit is press on esc
                        pygame.quit()
                        quit()
                    if event.type == pygame.MOUSEBUTTONDOWN:  # mouse button down is press on mouse
                        if 190 <= mouse_pos1[0] <= 470 and 400 <= mouse_pos1[1] <= 498:
                            print('replay button clicked!')
                            self.play_again_me = 1
                            self.msg = str(self.play_again_me)
                        elif 530 <= mouse_pos1[0] <= 880 and 390 <= mouse_pos1[1] <= 520:
                            print('exit button clicked!')
                            self.play_again_me = 0
                            self.msg = str(self.play_again_me)
                            pygame.quit()
                            quit()

            if score_me > score_friend:
                self.screen.fill(pygame.Color('white'))
                self.screen.blit(pygame.transform.scale(bg_sprite[10], (self.width, self.height)), (0, 0))
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bg_sprite[11], (390, 200)), 0),
                                 (325, 50))
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bongo_sprite[0], (700, 700)), 13),
                                 (125, 242))
                self.draw_text('YOU WIN', 512, 150, 50, 0, 0, 0)
                self.draw_text('SCORE ' + str(self.player_me.score), 512, 300, 50, 255, 255, 255)
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(button_sprite[1], (280, 98)), 0),
                                 (190, 400))
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(button_sprite[2], (350, 130)), 0),
                                 (530, 390))

                for event in pygame.event.get():  # ดูว่าเกิดeventอะไรขึ้น
                    if event.type == pygame.QUIT:  # type คือการกดคีย์บอร์ด #quit is press on esc
                        pygame.quit()
                        quit()
                    if event.type == pygame.MOUSEBUTTONDOWN:  # mouse button down is press on mouse
                        if 190 <= mouse_pos1[0] <= 470 and 400 <= mouse_pos1[1] <= 498:
                            print('replay button clicked!')
                            self.play_again_me = 1
                            self.msg = str(self.play_again_me)
                        elif 530 <= mouse_pos1[0] <= 880 and 390 <= mouse_pos1[1] <= 520:
                            print('exit button clicked!')
                            self.play_again_me = 0
                            self.msg = str(self.play_again_me)
                            pygame.quit()
                            quit()

            if score_me == score_friend:
                self.screen.fill(pygame.Color('white'))
                self.screen.blit(pygame.transform.scale(bg_sprite[12], (self.width, self.height)), (0, 0))
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(bg_sprite[13], (350, 130)), 0),
                                 (330, 85))
                self.draw_text('DRAW', 512, 150, 50, 255, 255, 255)
                self.draw_text('SCORE ' + str(self.player_me.score), 512, 300, 50, 255, 255, 255)
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(button_sprite[1], (280, 98)), 0),
                                 (190, 400))
                self.screen.blit(pygame.transform.rotate(pygame.transform.scale(button_sprite[2], (350, 130)), 0),
                                 (530, 390))

                for event in pygame.event.get():  # ดูว่าเกิดeventอะไรขึ้น
                    if event.type == pygame.QUIT:  # type คือการกดคีย์บอร์ด #quit is press on esc
                        pygame.quit()
                        quit()
                    if event.type == pygame.MOUSEBUTTONDOWN:  # mouse button down is press on mouse
                        if 190 <= mouse_pos1[0] <= 470 and 400 <= mouse_pos1[1] <= 498:
                            print('replay button clicked!')
                            self.play_again_me = 1
                            self.msg = str(self.play_again_me)
                        elif 530 <= mouse_pos1[0] <= 880 and 390 <= mouse_pos1[1] <= 520:
                            print('exit button clicked!')
                            self.play_again_me = 0
                            self.msg = str(self.play_again_me)
                            pygame.quit()
                            quit()

            pygame.display.update()

    def send_data(self, msg):
        print('msg', msg)
        data = str(self.net.game_id) + "," + str(self.net.id) + "," + str(self.game_state) + "," + str(msg)
        print('sent', data)
        reply = self.net.send(data)
        print('reply', reply)
        return reply

    @staticmethod
    def parse_data(data):
        data_split = data.split(":")
        game_data, player_data, word_data = [], '', ''
        if len(data_split) == 1:
            game_data = data.split(":")[0].split(",")
            return game_data, {}, {}

        elif len(data_split) == 2:
            game_data, player_data = data.split(":")[0].split(","), data.split(":")[1]
            player_list = player_data.split("|")
            player_dict = {}
            for player_string in player_list:
                player = player_string.split(",")
                player_dict[player[0]] = player[1:]
            return game_data, player_dict, {}

        elif len(data_split) == 3:
            game_data, player_data, word_data = data.split(":")[0].split(","), data.split(":")[1], data.split(":")[2]
            player_list = player_data.split("|")
            if len(word_data) > 0:
                word_list = word_data.split("|")
            else:
                word_list = []
            player_dict = {}
            word_dict = {}
            for player_string in player_list:
                player = player_string.split(",")
                player_dict[player[0]] = player[1:]
            for word_string in word_list:
                word_separated_data = word_string.split(",")
                word_dict[word_separated_data[0]] = word_separated_data
            print('gamedata;', game_data, 'player_dict:', player_dict, 'word_dict:', word_dict)
            return game_data, player_dict, word_dict

    def sync_data(self, game_data_list, player_data_dict, word_data_dict):
        print('game_data_list', game_data_list)
        self.game_state = int(game_data_list[1])
        if self.game_state == 0:
            self.lobby_count = int(game_data_list[2])

        elif self.game_state == 1:
            self.count_down_time = game_data_list[2]
            self.player_friend.name = game_data_list[3]

        elif self.game_state == 2:
            self.draw_state_friend = int(game_data_list[2])
            self.game_time = int(game_data_list[3])
            for player_id in player_data_dict:
                self.player_dict[player_id].score = player_data_dict[player_id][0]
            for word_data in word_data_dict:
                if word_data in self.word_mem:
                    self.word_mem[word_data].x_pos = x = int(word_data_dict[word_data][3])
                    self.word_mem[word_data].y_pos = y = int(word_data_dict[word_data][4])
                    self.word_mem[word_data].text_rect.topleft = (x, y)
                else:
                    self.word_mem[word_data] = Word(int(word_data_dict[word_data][0]),
                                                    int(word_data_dict[word_data][1]),
                                                    int(word_data_dict[word_data][2]),
                                                    int(word_data_dict[word_data][3]),
                                                    int(word_data_dict[word_data][4]))

            keys_to_keep = set(word_data_dict.keys()).intersection(set(self.word_mem.keys()))
            keys_to_play = set(self.word_mem.keys()).difference(set(word_data_dict.keys()))
            self.word_to_play_mem = {k: v for k, v in self.word_mem.items() if k in keys_to_play}
            if self.word_to_play_mem:
                self.explo_sound.play()
            self.word_mem = {k: v for k, v in self.word_mem.items() if k in keys_to_keep}

        elif self.game_state == 3:
            for player_id in player_data_dict:
                self.player_dict[player_id].score = player_data_dict[player_id][0]
                self.player_dict[player_id].play_again = player_data_dict[player_id][1]

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

    Stage 3:
    client data format:
        [game_id, client_id, client_game_state, play_again] 1 play again 0 not
    server data format:
        [game_id, game_state, : client_id, score, play_again | client_id, score, play_again]

    Restart Message:
        [game_id, restart, : client_id, score, play_again | client_id, score, play_again]
    """

    def draw_text(self, text, xpos, ypos, font_size, r, g, b):
        font = pygame.font.Font('Assets/font/pixelart.ttf', font_size)
        text_show = font.render(str(text), True, (r, g, b))
        text_show_rect = text_show.get_rect()
        text_show_rect.center = (xpos, ypos)
        self.screen.blit(text_show, text_show_rect)

    def draw_name_stroke(self, current_stroke):
        name_text = self.font.render(current_stroke, True, pygame.Color('black'))
        name_text_rect = name_text.get_rect()
        name_text_rect.topleft = (290, 270)
        self.screen.blit(name_text, name_text_rect)

    def draw_bongo_cat(self, png, user):
        if user == 0:  # draw me
            self.screen.blit(pygame.transform.scale(png, (300, 300)), (self.player_x_me, self.player_y_me))
        if user == 1:  # draw friend
            self.screen.blit(pygame.transform.flip(pygame.transform.scale(png, (300, 300)), True, False),
                             (self.player_x_friend, self.player_y_friend))

    def bongo_animation(self, bongo_state, event):  # bongo state which folder (me or friend)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.draw_state_me = 2
                self.draw_bongo_cat(bongo_state[self.draw_state_me], 0)
            else:
                if self.draw_index % 2 == 0:
                    self.draw_state_me = 4
                    self.draw_bongo_cat(bongo_state[self.draw_state_me], 0)
                if self.draw_index % 2 == 1:
                    self.draw_state_me = 6
                    self.draw_bongo_cat(bongo_state[self.draw_state_me], 0)
                self.draw_index += 1

    def bongo_animation_friend(self, bongo_state):
        self.draw_bongo_cat(bongo_state[self.draw_state_friend], 1)

    def display_VFX(self, w, frame):
        self.screen.blit(pygame.transform.scale(self.vfx_boom[frame], (200, 200)), (w.x_pos - 50, w.y_pos - 60))

    def draw_text_waiting(self, text, xpos, ypos):
        font = pygame.font.Font("Assets/font/pixelart.ttf", 35)
        # font = pygame.font.Font("pixelfont", 40, bold = True)
        text_a = font.render(text, True, pygame.Color(102, 0, 102))

        text_a_rect = text_a.get_rect()
        text_a_rect.topleft = (xpos, ypos)
        self.screen.blit(text_a, text_a_rect)

    def draw_timer(self, time):
        time_text = self.font.render(str(time), True, pygame.Color('black'))
        time_text_rect = time_text.get_rect()
        time_text_rect.topright = (1010, 10)
        self.screen.blit(time_text, time_text_rect)

    def draw_name_me(self):
        name_text = self.font.render('MEOW ' + self.player_me.name, True, pygame.Color('black'))
        name_text_rect = name_text.get_rect()
        name_text_rect.topleft = (10, 10)
        self.screen.blit(name_text, name_text_rect)

    def draw_name_friend(self):
        name_text = self.font.render('MEOW ' + self.player_friend.name, True, pygame.Color('black'))
        name_text_rect = name_text.get_rect()
        name_text_rect.topright = (1014, 10)
        self.screen.blit(name_text, name_text_rect)

    def draw_score_me(self, score):
        score_text = self.font.render('SCORE: ' + str(score), True, pygame.Color('black'))
        score_text_rect = score_text.get_rect()
        score_text_rect.topleft = (10, 50)
        self.screen.blit(score_text, score_text_rect)

    def draw_score_friend(self, score):
        score_text = self.font.render('SCORE: ' + str(score), True, pygame.Color('black'))
        score_text_rect = score_text.get_rect()
        score_text_rect.topright = (1014, 50)
        self.screen.blit(score_text, score_text_rect)

    def draw_current_stroke(self, current_stroke):
        score_text = self.font.render(current_stroke, True, pygame.Color('black'))
        score_text_rect = score_text.get_rect()
        score_text_rect.midbottom = (512, 710)
        self.screen.blit(score_text, score_text_rect)

    def draw_connected_player_count(self, player_count):
        font = pygame.font.Font('Assets/font/pixelmix_bold.ttf', 35)
        text = font.render('(' + str(player_count) + '/2)', True, pygame.Color(102, 0, 102))
        text_rect = text.get_rect()
        text_rect.center = (700, 252)
        self.screen.blit(text, text_rect)

    def draw_countdown_timer(self, time):
        font = pygame.font.Font('Assets/font/pixelmix.ttf', 70)
        text = font.render(time, True, pygame.Color('black'))
        if time == '1':
            text = font.render(time + '!', True, pygame.Color('black'))
        text_rect = text.get_rect()
        text_rect.center = (int(self.width / 2), int(self.height / 2))
        self.screen.blit(text, text_rect)

    def draw_text_result(self, text, xpos, ypos):
        font = pygame.font.Font("Assets/font/pixelart.ttf", 50)
        text_a = font.render(text, True, pygame.Color(255, 255, 255))
        text_a_rect = text_a.get_rect()
        text_a_rect.topright = (xpos, ypos)
        self.screen.blit(text_a, text_a_rect)

    def print_move_word(self, w):
        self.screen.blit(w.text, w.text_rect)
        # w.text_rect.move_ip(0, w.fall_speed)

    def print_move_matching_word(self, w):
        self.screen.blit(w.matching_text, w.matching_text_rect)
        # w.matching_text_rect.move_ip(0, w.fall_speed)
