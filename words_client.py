import random
import pygame
from word_library import word_set


class Word:

    def __init__(self, word_id, word_code, fall_speed, x_pos, y_pos):
        self.x_pos = int(x_pos)
        self.y_pos = int(y_pos)
        self.font = pygame.font.Font('freesansbold.ttf', 32)
        self.start_match = False
        self.fall_speed = int(fall_speed)
        self.word = word_set[int(word_code)]
        self.text_width, self.text_height = self.font.size(self.word)
        self.matching_text = self.font.render("", True, pygame.Color('black'))
        self.matching_text_rect = self.matching_text.get_rect()
        self.text = self.font.render(self.word, True, pygame.Color('black'))
        self.text_rect = self.text.get_rect()
        self.text_rect.topleft = (self.x_pos, self.y_pos)
        self.id = int(word_id)

    def match_text(self, span):
        start, end = span
        matching_word = self.word[start:end]
        self.matching_text = self.font.render(matching_word, True, pygame.Color('green'))
        self.matching_text_rect = self.matching_text.get_rect()
        self.matching_text_rect.topleft = self.text_rect.topleft

    def unmatch_text(self):
        self.matching_text = self.font.render("", True, pygame.Color('black'))
        self.matching_text_rect = self.matching_text.get_rect()