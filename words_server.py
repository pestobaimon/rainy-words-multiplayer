import random
import pygame
from word_library import *


class Word:

    def __init__(self, word_id, word_code):
        if self.word_code[0] == 'e':
            self.word = easy_word[word_code]
        elif self.word_code[0] == 'h':
            self.word = hard_word[word_code]

        self.font = pygame.font.Font('freesansbold.ttf', 32)
        self.start_match = False
        self.fall_speed = random.randint(4, 8)
        self.text_width, self.text_height = self.font.size(self.word)
        self.x_offset = random.randint(0, 1024 - self.text_width)
        self.matching_text = self.font.render("", True, pygame.Color('black'))
        self.matching_text_rect = self.matching_text.get_rect()
        self.text = self.font.render(self.word, True, pygame.Color('black'))
        self.text_rect = self.text.get_rect()
        self.text_rect.topleft = (self.x_offset, -50)
        self.disabled = False
        self.id = word_id


    def match_text(self, span):
        start, end = span
        matching_word = self.word[start:end]
        self.matching_text = self.font.render(matching_word, True, pygame.Color('green'))
        self.matching_text_rect = self.matching_text.get_rect()
        self.matching_text_rect.topleft = self.text_rect.topleft

    def unmatch_text(self):
        self.matching_text = self.font.render("", True, pygame.Color('black'))
        self.matching_text_rect = self.matching_text.get_rect()

    def disable(self):
        self.disabled = True
