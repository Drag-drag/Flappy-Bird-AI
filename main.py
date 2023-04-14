import pygame
from pygame.locals import *
import sys
import random
from enum import Enum
import neat

WIDTH = 864
HEIGHT = 936
FPS = 120
PIPE_GAP = 150

ground_scroll = 0
scroll_speed = 4
pipe_frequency = 2000 # milliseconds
last_pipe = pygame.time.get_ticks()
pass_pipe = False

SCORE = 0
generation = 0

class BirdState(Enum):
    JUMP = 1
    FALL = 2


class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        self.index = 0
        self.counter = 0
        for i in range(1, 4):
            img = pygame.image.load(f'img/bird{i}.png')
            self.images.append(img)

        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.velocity = 0
        self.state = BirdState.FALL
        self.jumped = False

    def draw(self, screen):
        screen.blit(self.image, (self.rect.x, self.rect.y))

    def update(self):

        self.velocity += 0.5
        if self.velocity > 8:
            self.velocity = 8
        if self.rect.bottom < 768:
            self.rect.y += int(self.velocity)

        # handle the animation
        self.counter += 1
        flap_cooldown = 5

        if self.counter > flap_cooldown:
            self.counter = 0
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
        self.image = self.images[self.index]

        # rotate animation
        self.image = pygame.transform.rotate(self.images[self.index], -2 * self.velocity)

    def jump(self):
        self.velocity = -10
        self.state == BirdState.FALL
        self.jumped = True
            


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/pipe.png')
        self.rect = self.image.get_rect()
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect.bottomleft = [x, y - PIPE_GAP//2]
        else:
            self.rect.topleft = [x, y + PIPE_GAP//2]

    def update(self):
        self.rect.x -= scroll_speed
        


def calc_dist(a, b):
    return b - a


def run_game(genomes, config):

    global ground_scroll, last_pipe, SCORE, pass_pipe, generation

    generation += 1
    birds = []
    nets = []
    pipe_index = 0

    for i, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        g.fitness = 0

        birds.append(Bird(100, HEIGHT // 2))

    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Flappy bird AI')
    clock = pygame.time.Clock()

    bird = pygame.sprite.Group()
    pipe_group = pygame.sprite.Group()

    score_font = pygame.font.SysFont("Roboto Condensed", 40)
    generation_font = pygame.font.SysFont("Roboto Condensed", 50)

    bg = pygame.image.load('img/bg.png')
    ground = pygame.image.load('img/ground.png')

    btm_pipe = Pipe(WIDTH, HEIGHT // 2, -1)
    top_pipe = Pipe(WIDTH, HEIGHT // 2, 1)
    pipe_group.add(btm_pipe)
    pipe_group.add(top_pipe)

    while True:

        screen.blit(bg, (0, 0))
        screen.blit(ground, (ground_scroll, 768))
        ground_scroll -= scroll_speed

        for i, bird in enumerate(birds):
            bird.draw(screen)
            bird.update()
            genomes[i][1].fitness += 0.1
            

        pipe_group.draw(screen)
        pipe_group.update()

        score_label = score_font.render("Очки: " + str(SCORE), True, (50, 50, 50))
        score_label_rect = score_label.get_rect()
        score_label_rect.center = (WIDTH - 100, 50)
        screen.blit(score_label, score_label_rect)


        #  # check collisions
        # if pygame.sprite.groupcollide(bird_group, pipe_group, True, False) or bird.rect.top < 0 or bird.rect.bottom > 768:
        #     bird.kill()

        for i, pipe in enumerate(pipe_group.sprites()):
            for j, bird in enumerate(birds):
                if bird.rect.colliderect(pipe.rect) or bird.rect.top <= 0 or bird.rect.bottom >= 768:
                    genomes[j][1].fitness -= 10
                    birds.pop(j)
                    genomes.pop(j)
                    nets.pop(j)
            
            if pipe.rect.right < 0:
                pipe_index -= 1
                pipe.kill()
        
        if len(birds) == 0:
            SCORE = 0
            break

        # check the score
        for i, pipe in enumerate(pipe_group.sprites()):
            for j, bird in enumerate(birds):
                if bird.rect.left > pipe.rect.left \
                    and bird.rect.right < pipe.rect.right \
                    and not(pass_pipe):
                    pass_pipe = True
                if pass_pipe:
                    if bird.rect.left > pipe.rect.right:
                        pass_pipe = False
                        SCORE += 1
                        genomes[j][1].fitness += 5
                        pipe_index += 2

        # generate new pipes
        time_now = pygame.time.get_ticks()
        if pipe_group.sprites()[0].rect.x == 500 or pipe_group.sprites()[0].rect.x == 100:
            pipe_height = random.randint(-100, 100)
            btm_pipe = Pipe(WIDTH, HEIGHT // 2 + pipe_height, -1)
            top_pipe = Pipe(WIDTH, HEIGHT // 2 + pipe_height, 1)
            pipe_group.add(btm_pipe)
            pipe_group.add(top_pipe)
            last_pipe = time_now

        for i, bird in enumerate(birds):
            output = nets[i].activate((bird.rect.y,
                                       calc_dist(bird.rect.x, pipe_group.sprites()[0].rect.x),
                                       calc_dist(bird.rect.y, pipe_group.sprites()[pipe_index].rect.bottom),
                                       calc_dist(bird.rect.y, pipe_group.sprites()[pipe_index+1].rect.top)))

            if output[0] > 0.5:
                bird.state = BirdState.JUMP
                bird.jumped = False
                bird.jump()
                
                genomes[i][1].fitness -= 1  # every jump lowers the fitness (assuming it's false jump)
        

        generation_label = generation_font.render("Поколение: " + str(generation), True, (50, 50, 50))
        generation_label_rect = generation_label.get_rect()
        generation_label_rect.center = (WIDTH//2, HEIGHT//2-400)
        screen.blit(generation_label, generation_label_rect)


        if abs(ground_scroll) > 35:
            ground_scroll = 0


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    # setup config
    config_path = "./config-feedforward.txt"
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)

    # init NEAT
    p = neat.Population(config)

    # run NEAT
    p.run(run_game, 1000)
