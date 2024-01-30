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
from scripts.UI import Heart, Text

class Game:
    def __init__(self):
        '''
        initializes Game
        '''
        pygame.init()

        x = (1140, 810)

        # change the window caption
        pygame.display.set_caption("CleanUp!")
        # create window
        self.screen = pygame.display.set_mode((1140, 810)) # (640, 480), (960, 720), (768, 576)
        self.display = pygame.Surface(x, pygame.SRCALPHA) # render on smaller resolution then scale it up to bigger screen

        self.display2 = pygame.Surface(x)


        self.clock = pygame.time.Clock()
        
        self.movement = [False, False, False, False]

        self.assets = {
            'background': load_image('black.jpg'),
            'enemy/idle': Animation(load_images('entities/enemy/idle')),
            'player/idle': Animation(load_images('entities/player/idle')),
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
        self.player = Player(self, (self.display2.get_width()/2, self.display2.get_height()/2), (32, 32))

        # initalizing tilemap
        self.tilemap = Tilemap(self, tile_size=16)

        self.sparks = []
        self.projectiles = []

        # tracking level
        self.level = 0
        self.max_level = len(os.listdir('data/maps')) # max level,
        # loading the level

        # screen shake
        self.screenshake = 0

        self.cooldown = 0
        self.angle_count = 0
        self.horizontal_count = 0
        self.rotations = 0 # rotations based on camera movement
        self.score = 0
        self.left_key_pressed = False
        self.right_key_pressed = False
        self.gameOver = 0
        self.enemies = [] 
        self.spawn_timer = 0
        self.spawn_interval = 10

        self.enemyRotation = 0

        self.counter = 0
        self.start = 0

        self.load_level(0)  # self.load_level(self.level), hard coding to 1 atm
        
        
    def spawn_enemy(self):


        #for i in range(0,):
        #    if i == 0:
        x = random.randint(50, self.screen.get_width() - 50)
        y = random.randint(60, self.screen.get_height() + 20)


        self.enemies.append(Enemies(self, [x, y], [16, 16]))

    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        self.gameOver = 0

        # keep track
        self.particles = []

        # creating 'camera' 
        self.scroll = [0, 0]

        self.dead = 0 # gives player 3 lives, -2, -1, 0

        self.rotations = 0 # rotations based on camera movement
        self.movement = [False, False, False, False]

        # transition for levels
        self.transition = -30

        self.spawn_timer = 0
        self.spawn_interval = 100

        self.score = 0
        self.counter = 0
        self.start = 0 # dont spawn enemies until player moves

        # spawn the ememies
        self.enemies = [] # clear enemies

        for spawner in self.tilemap.extract([('spawners', 0)]):
            if spawner['variant'] == 0: 
                self.player.pos = [600, 400] # top left [50,60]   # middle [600, 400]
                # reset
                self.rotations = 0 # rotations based on camera movement
                self.movement = [False, False, False, False]
                self.left_key_pressed = False
                self.right_key_pressed = False


    def run(self):
        '''
        runs the Game
        '''

        #pygame.mixer.music.load('data/music.mp3')
        #pygame.mixer.music.set_volume(0.5)
        #pygame.mixer.music.play(-1)

        #self.sfx['ambience'].play(-1)

        # creating an infinite game loop
        while True:
            self.display.fill((0, 0, 0, 0))    # black outlines
            self.display.fill((0,0,0,0))
            # clear the screen for new image generation in loop
            self.screen.blit(self.assets['background'], (0,0)) # no outline


            self.screenshake = max(0, self.screenshake-1) # resets screenshake value

            if self.dead: 
                self.dead += 1
                if self.dead >= 10: # to make the level transitions smoother
                    self.transition = min(self.transition + 1, 20) # go as high as it can without changing level
                if self.dead > 30: # timer that starts when you die
                    # self.level = 0
                    offsetText = 3
                    replay = Text("Press L to Restart", pos=(self.display.get_width() /2 - 120, self.display.get_height() // 2 - 13))
                    replay.render(self.display, 40)
                    replay2 = Text("Press L to Restart", pos=(self.display.get_width() /2 - 120 + offsetText, self.display.get_height() // 2 - 13 + offsetText))
                    replay2.render(self.display, 40, color=(255,255,255))
                    self.movement = [False, False, False, False]
                    self.gameOver = 1

            # scroll = current scroll + (where we want the camera to be - what we have/can see currently) 
            self.scroll[0] = self.display.get_width()/ 2 / 30 
            self.scroll[1] = self.display.get_height()/ 2 / 30
            # fix the jitter
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            # spawn enemies
            if self.start:
                self.spawn_timer += 1
            if self.spawn_timer >= self.spawn_interval and not self.dead:
                self.spawn_enemy()
                self.spawn_timer = 0
                self.spawn_interval =  30 #make dynamic


            self.enemyRotation = (self.enemyRotation + 1) % 360


            trueWidth =  self.screen.get_width() + 30
            trueHeight = self.screen.get_height() + 20

            # render the enemies
            for enemy in self.enemies.copy():
                kill =  enemy.update(self.tilemap, (1,1))
                enemy.render(self.display, self.enemyImg, self.enemyRotation, offset=render_scroll)
                #pygame.draw.rect(self.display, (255, 0, 0), (enemy.pos[0] - render_scroll[0] - 30, enemy.pos[1] - render_scroll[1] - 40, enemy.size[0], enemy.size[1]), 3)
                if kill: # if enemies update fn returns true [**]d
                    self.enemies.remove(enemy) 
                    self.score += 1
                if enemy.pos[1] >= trueHeight:
                    self.enemies.remove(enemy) 
                if enemy.pos[0] < 50:
                     self.enemies.remove(enemy)
                if enemy.pos[1] < 60:
                     self.enemies.remove(enemy) 
                if enemy.pos[0] > trueWidth:
                    self.enemies.remove(enemy) 
                if self.player.rect().colliderect(enemy): # player collides with enemy
                    self.dead += 1 # die
            
            
            if self.dead:
                # self.sfx['hit'].play()
                self.cooldown = 150
                self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                for i in range(30): # when projectile hits player
                    # on death sparks
                    angle = random.random() * math.pi * 2 # random angle in a circle
                    speed = random.random() * 5
                    self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))    # fix sparks
                    # on death particles
                    self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))
        

            if not self.dead and self.start == 1:
                # update player movement and score counter
                self.counter += 1
                self.score = self.counter // 60
                self.player.update(self.tilemap, ((self.movement[1] - self.movement[0]) * self.player.speed, (self.movement[3] - self.movement[2]) * self.player.speed))
            self.player.render(self.display,  self.playerImg, self.rotations, offset=render_scroll, spread=1.2)
            #pygame.draw.rect(self.display, (255, 255, 0), (self.player.pos[0] - render_scroll[0] - 33, self.player.pos[1] - render_scroll[1] - 50, self.player.size[0], self.player.size[1]), 3)

            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1] 
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img if projectile[1] > 0 else pygame.transform.flip(img, True, False), (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1])) # spawns it the center of the projectile
                
                # keep this but change it to the borders of the map, also might want some obsticles later
                if self.tilemap.solid_check(projectile[0]): # if location is a solid tile
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random())) # (math.pi if projectile[1] > 0 else 0), sparks bounce in oppositie direction if hit wall which depends on projectile direction
                elif projectile[2] > 360: #if timer > 6 seconds
                    self.projectiles.remove(projectile)
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)  # apply screenshake, larger wont be overrided by a smaller screenshake
                        for i in range(30): # when projectile hits player
                            # on death sparks
                            angle = random.random() * math.pi * 2 # random angle in a circle
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random())) 
                            # on death particles
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))
           
                                    
            #hp_1 = Heart(self.assets['heart'].copy(), [13, 19], 15)
            #hp_2 = Heart(self.assets['heart'].copy(), [30, 19], 15)
            #hp_3 = Heart(self.assets['heart'].copy(), [47, 19], 15)
            #if self.dead <= 0 and self.dead < 1:
            #    hp_1.update()
            #    hp_1.render(self.display_black)
            #if self.dead <= -1:
            #    hp_2.update()
            #    hp_2.render(self.display_black)
            #if self.dead <= -2:
            #    hp_3.update()
            #    hp_3.render(self.display_black)
            
            level_bar = Text("Score: " + str(self.score), pos=(self.display.get_width() // 2 -30, 13))
            level_bar.render(self.display, 22)
            

            # black ouline based on display_black
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0)) # 180 opaque, 0 transparent
            self.display2.blit(display_sillhouette, (0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display2.blit(display_sillhouette, offset) # putting what we drew onframe back into display


            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3 # making the parlitcle move back and forth smooth'y
                if kill:
                    self.particles.remove(particle)


            for event in pygame.event.get():
                if event.type == pygame.QUIT: # have to code the window closing
                    pygame.quit()
                    sys.exit()
                if self.gameOver:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_l:
                        self.load_level(self.level)
                else: 
                    if event.type == pygame.KEYDOWN:
                        self.start = 1
                        if event.key == pygame.K_a: # referencing WASD
                            self.left_key_pressed = True
                        if event.key == pygame.K_d:
                            self.right_key_pressed = True
                    elif event.type == pygame.KEYUP:
                        if event.key == pygame.K_a:
                            self.left_key_pressed = False
                        elif event.key == pygame.K_d:
                            self.right_key_pressed = False

            if self.left_key_pressed:
                self.rotations = (self.rotations + 1.6 ) % 360
            if self.right_key_pressed:
                self.rotations = (self.rotations - 1.6 ) % 360

            #self.movement[2] = True
            if self.rotations > 90 and self.rotations < 180:
                self.movement[0] = True
                self.movement[3] = True
                self.movement[1] = False
                self.movement[2] = False
            if self.rotations < 90 and self.rotations > 0:
                self.movement[0] = True
                self.movement[2] = True
                self.movement[3] = False
                self.movement[1] = False
            if self.rotations > 180 and self.rotations < 270:
                self.movement[1] = True 
                self.movement[3] = True
                self.movement[0] = False
                self.movement[2] = False
            if self.rotations > 270: # last case as to not activate unless actually in state
                self.movement[1] = True
                self.movement[2] = True
                self.movement[0] = False
                self.movement[3] = False


            self.display2.blit(self.display, (0, 0)) # black 


            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), screenshake_offset) # render (now scaled) display image on big screen
            
            pygame.display.update()
            self.clock.tick(60) # run at 60 fps, like a sleep

# returns the game then runs it
Game().run()
