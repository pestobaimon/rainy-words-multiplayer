import pygame
from multiprocessing import Pipe
pygame.init()

font = pygame.font.Font('freesansbold.ttf', 32)


p_output, p_input = Pipe()


x = p_output.recv()

print(x)