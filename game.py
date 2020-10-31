from words_server import Word
from timer import Timer
from player import Player
from word_library import word_set
import random
import pygame
import re


def add_new_word(word_dict):
    key = random.choice(list(word_set.keys()))
    word_dict[key] = Word(word_set[key])
    return word_set[key]


class Game:

    def __init__(self):
        pygame.init()
        self.width = 1024
        self.height = 720
        self.font = pygame.font.Font('freesansbold.ttf', 32)
        self.player_me = ""
        self.screen = pygame.display.set_mode((self.width, self.height))

    def run(self):
        clock = pygame.time.Clock()

        running = True

        word_mem = []

        timer = Timer()

        backspace_clock = Timer()

        while running:
            framerate = clock.tick(30)
            backspace_clock.tick()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_BACKSPACE] and len(self.player_me.keystrokes) > 0 and backspace_clock.time >= 2:
                backspace_clock.reset()
                self.player_me.keystrokes = self.player_me.keystrokes[:-1]
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                elif event.type == pygame.KEYDOWN:
                    if event.unicode != '\r' and event.unicode != '\b' and event.unicode.isalpha():
                        self.player_me.keystrokes += event.unicode
                    elif event.unicode == '\r':
                        self.player_me.confirm_key = True
                    # elif len(player1.keystrokes) > 0:
                    #     player1.keystrokes = player1.keystrokes[:-1
            self.screen.fill(pygame.Color('white'))
            self.draw_score(self.player_me.score)
            self.draw_current_stroke(self.player_me.keystrokes)

            if len(word_mem) <= 1:
                timer.tick()
            if timer.time >= 90:
                timer.reset()
                add_new_word(word_mem)

            removed_words = []

            for word in word_mem:

                if self.player_me.keystrokes == word.word and self.player_me.confirm_key:
                    self.erase_word(word)
                    self.player_me.score += 1
                    removed_words.append(word)
                    continue

                if self.player_me.keystrokes == '':
                    s = False
                else:
                    s = re.search("^" + self.player_me.keystrokes, word.word)

                if s:
                    word.match_text(s.span())
                    word.start_match = True
                    self.print_move_word(word)
                    self.print_move_matching_word(word)
                elif word.start_match:
                    word.start_match = False
                    word.unmatch_text()
                    self.print_move_word(word)
                else:
                    self.print_move_word(word)

                if word.text_rect.bottomleft[1] > 720:
                    removed_words.append(word)
                    continue

            if len(removed_words) > 0:
                print('removed')
                word_mem = [i for i in word_mem if i not in removed_words]

            if self.player_me.confirm_key:
                self.player_me.keystrokes = ''
                self.player_me.confirm_key = False
            pygame.display.update()

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

    def print_move_word(self, w):
        self.screen.blit(w.text, w.text_rect)
        w.text_rect.move_ip(0, w.fall_speed)

    def print_move_matching_word(self, w):
        self.screen.blit(w.matching_text, w.matching_text_rect)
        w.matching_text_rect.move_ip(0, w.fall_speed)

    def erase_word(self, w):
        pygame.draw.polygon(self.screen, pygame.Color('white'), [w.text_rect.topleft, w.text_rect.bottomleft, w.text_rect.topright,
                                            w.text_rect.bottomright])

    def resetGame(self):
        pass
    def resetScore(self):
        pass

game = Game()
game.run()

