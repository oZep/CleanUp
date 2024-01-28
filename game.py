import sys
import os
import math
import random
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemies
from scripts.tilemap import Tilemap
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.UI import Heart, Levelbar

class Game:
    def __init__(self):
        '''
        initializes Game
        '''
        pygame.init()

        # change the window caption
        pygame.display.set_caption("10 Levels of Hell")
        # create window
        self.screen = pygame.display.set_mode((640, 480)) # (640, 480), (960, 720), (768, 576)
        self.display_black = pygame.Surface((320, 240), pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen
        self.display_none = pygame.Surface((320, 240), pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen

        self.display_2 = pygame.Surface((320, 240))


        self.clock = pygame.time.Clock()
        
        self.movement = [False, False, False, False]

        self.assets = {
            'player': load_image('entities/player/player.png'),
            'background': load_image('background.png'),
            'heart': load_image('UI/health.png'),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
        }

        # adding sound
        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }

        self.playerImg = load_images('entities/player/idle')
        self.enemyImg = load_images('entities/enemy/idle') # just make shooting particle effects
        
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)

        #self.clouds = Clouds(self.assets['clouds'], count=16)

        # initalizing player
        self.player = Player(self, (self.display_none.get_width()/2, self.display_none.get_height()/2), (15, 15))

        # initalizing tilemap
        self.tilemap = Tilemap(self, tile_size=16)

        # tracking level
        self.level = 0
        self.max_level = len(os.listdir('data/maps')) # max level,
        # loading the level
        self.load_level(0)  # self.load_level(self.level), hard coding to 1 atm

        # screen shake
        self.screenshake = 0

        self.cooldown = 0
        self.angle_count = 0
        self.horizontal_count = 0
        self.rotations = 0 # rotations based on camera movement


    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')

        # keep track
        self.particles = []

        # creating 'camera' 
        self.scroll = [0, 0]

        self.dead = -2  # gives player 3 lives, -2, -1, 0

        # transition for levels
        self.transition = -30
        
        # spawn the ememies
        self.enemies = [] # make this random generate and increase spawn # as game time goes on

        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2), ('spawners', 3)]):
            if spawner['variant'] == 0: 
                self.player.pos = spawner['pos']
            else:
                self.enemies.append(Enemies(self, spawner['pos'], (21, 31)))
                # spawn the ememies, make random

    def run(self):
        '''
        runs the Game
        '''
        pygame.mixer.music.load('data/music.mp3')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)

        # creating an infinite game loop
        while True:
            self.display_black.fill((0, 0, 0, 0))    # black outlines
            self.display_none.fill((0,0,0,0))
            # clear the screen for new image generation in loop
            self.display_2.blit(self.assets['background'], (0,0)) # no outline

            self.screenshake = max(0, self.screenshake-1) # resets screenshake value

            if self.dead >= 1: # get hit 3 times
                self.dead += 1
                if self.dead >= 10: # to make the level transitions smoother
                    self.transition = min(self.transition + 1, 30) # go as high as it can without changing level
                if self.dead > 40: # timer that starts when you die
                    # self.level = 0
                    self.load_level(self.level) # start at level 0 again. self.load_level(0)
            

            # scroll = current scroll + (where we want the camera to be - what we have/can see currently) 
            self.scroll[0] = self.display_none.get_width()/2 / 30 + 3 # x axis
            self.scroll[1] = self.display_none.get_height()/2/ 30 + 3

            # fix the jitter
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display_none, self.enemyImg, self.rotations, offset=render_scroll)

            # render the enemies
            for enemy in self.enemies.copy():
                kill =  enemy.update(self.tilemap, (0,0))
                enemy.render(self.display_none, self.enemyImg, self.rotations, offset=render_scroll)
                if kill: # if enemies update fn returns true [**]
                    self.enemies.remove(enemy) 
                if self.player.rect().colliderect(enemy): # player collides with enemy
                    self.dead += 1 # die
                    self.sfx['hit'].play()
                    self.cooldown = 150
                    self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                    for i in range(30): # when projectile hits player
                        # on death sparks
                        angle = random.random() * math.pi * 2 # random angle in a circle
                        speed = random.random() * 5
                        self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))    # fix sparks
                        # on death particles
                        self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))


            # Reduce timer
            if self.cooldown > 0:
                    self.cooldown -= 1

            if self.dead != 1:
                # update player movement
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], self.movement[3] - self.movement[2]))
                self.player.render(self.display_black,  self.playerImg, self.rotations, offset=render_scroll)

            # render/spawn bullet projectiles
            # [[x, y], direction, timer]
            # make direction go based on angle
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1] 
                projectile[2] += 1
                img = self.assets['projectile']
                self.display_black.blit(img if projectile[1] > 0 else pygame.transform.flip(img, True, False), (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1])) # spawns it the center of the projectile
                
                if projectile[2] > 360: #if timer > 6 seconds
                    self.projectiles.remove(projectile)
                                    
            hp_1 = Heart(self.assets['heart'].copy(), [13, 19], 15)
            hp_2 = Heart(self.assets['heart'].copy(), [30, 19], 15)
            hp_3 = Heart(self.assets['heart'].copy(), [47, 19], 15)
            if self.dead <= 0 and self.dead < 1:
                hp_1.update()
                hp_1.render(self.display_black)
            if self.dead <= -1:
                hp_2.update()
                hp_2.render(self.display_black)
            if self.dead <= -2:
                hp_3.update()
                hp_3.render(self.display_black)

            level_bar = Levelbar(self.level, pos=(self.display_none.get_width() // 2 - 25, 13))
            level_bar.render(self.display_black, 22)
            

            # black ouline based on display_black
            display_mask = pygame.mask.from_surface(self.display_black)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0)) # 180 opaque, 0 transparent
            self.display_2.blit(display_sillhouette, (0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset) # putting what we drew onframe back into display


            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display_none, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3 # making the parlitcle move back and forth smooth'y
                if kill:
                    self.particles.remove(particle)


            for event in pygame.event.get():
                if event.type == pygame.QUIT: # have to code the window closing
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a: # referencing WASD
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True # make going forward alway constant
                if event.type == pygame.KEYUP: # when key is released
                    if event.key == pygame.K_a: 
                        self.movement[0] = False
                    if event.key == pygame.K_d: 
                        self.movement[1] = False
            
            self.display_2.blit(self.display_black, (0, 0)) # black 
            self.display_2.blit(self.display_none, (0,0))
            
            # implementing transition
            if self.transition:
                transition_surf = pygame.Surface(self.display_none.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display_none.get_width() // 2, self.display_none.get_height() // 2), (30 - abs(self.transition)) * 8) # display center of screen, 30 is the timer we chose, 30 * 8 = 180
                transition_surf.set_colorkey((255, 255, 255)) # making the circle transparent now
                self.display_2.blit(transition_surf, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset) # render (now scaled) display image on big screen
            pygame.display.update()
            self.clock.tick(60) # run at 60 fps, like a sleep

# returns the game then runs it
Game().run()