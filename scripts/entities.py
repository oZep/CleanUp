import pygame
import math
import random

from scripts.particle import Particle
from scripts.spark import Spark
from scripts.UI import Heart

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        '''
        initializes entities
        (game, entitiy type, position, size)
        '''
        self.game = game
        self.type = e_type
        self.pos = list(pos) #make sure each entitiy has it's own list, (x,y)
        self.size = size
        self.velocity = [0,0]
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        self.action = ''
        self.anim_offset = (-3, -3) #renders with an offset to pad the animation against the hitbox
        self.flip = False
        
        self.set_action('idle') #**

        self.last_movement = [0, 0]

    def rect(self):
        '''
        creates a rectangle at the entitiies current postion
        '''
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        '''
        sets a new action to change animation
        (string of animation name) -> animation
        '''
        if action != self.action: # if action has changed
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()


    
    def update(self, tilemap, movement=(0,0)):
        '''
        updates frames and entitiy position 
        '''
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False} # this value will be reset every frame, used to stop constant increase of velocity

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect() # getting the entities rectange
        # move tile based on collision on y axis
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0: # if moving right and you collide with tile
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0: # if moving left
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        
        # Note: Y-axis collision handling comes after X-axis handling
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()  # Update entity rectangle for y-axis handling
        # move tile based on collision on y axis
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0: # if moving right and you collide with tile
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0: # if moving left
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

        entity_rect = self.rect()  # Update entity rectangle for y-axis handling

        # find when to flip img for animation
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement # keeps track of movement

        self.animation.update() # update animation


    def render(self, surf, offset={0,0}):
        '''
        renders entitiy asset
        '''
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1])) # fliping agasint horizontal axis



class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates player entity
        (game, position, size)
        '''
        super().__init__(game,'player', pos, size)
        self.dashing = 0

    def update(self, tilemap, movement=(0,0)):
        '''
        updates players animations depending on movement
        '''
        super().update(tilemap, movement=movement)

        if abs(self.dashing) in (60, 50): # if at start or end of dash
            for i in range(20): # do 20 times
                # for burst of particles
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5 # random from 0.5 to 1
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        # dash cooldown
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        # dash mechanism (only works in first 10 frames of 'dashing')

        # Will have to change to go in the direction of the mouse
        if abs(self.dashing) > 50:
            # need where we want to dash towards
            if self.direction == 'L': # Left
                self.velocity[0] = 8 
            if self.direction == 'J':
                self.velocity[0] = -8 
            if self.direction == 'I':
                 self.velocity[1] = -8 
            if self.direction == 'K':
                 self.velocity[1] = 8        
            if abs(self.dashing) == 51: # slow down dash after 10 frames
                self.velocity[0] *= 0.01
                self.velocity[1] *= 0.01  # goes to 0, but never allows player to move downward
            # trail of particles in the middle of dash
            pvelocity = [abs(self.dashing)/self.dashing * random.random() * 3, 0] # particles move in the direction of the dash
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
    
        if movement[0] != 0: # if moving horizontally
            self.set_action('run')
        elif movement[1] > 0:
            self.set_action('runDOWN')
        elif movement[1] < 0:
            self.set_action('runUP')
        else:
            self.set_action('idle')

        if abs(self.velocity[0]) < 0.1: # stops small sliding across screen after dash
            self.velocity[0] = 0
        if abs(self.velocity[1]) < 0.1:
            self.velocity[1] = 0


    def render(self, surf, offset={0,0}):
        '''
        partly overriding rendering for dashing
        '''
        if abs(self.dashing) <= 50: # not in first 10 frames of dash
            super().render(surf, offset=offset) # show player

    
    def dash(self, direction):
        '''
        makes the player dash
        (direction) 'I' for up, 'J'/'L' for right/left, 'K' for down
        '''
        self.direction = direction
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60 # how long the dash is + it's direction
                self.set_action('slide')
            

class Enemies(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates the enemies
        (game, position: tuple, size)
        '''
        super().__init__(game, 'skele', pos, size)
        self.walking = 1
        self.speed = 1 # enemy speed
        self.timer = 0 # enemy shooting timer
    
    def update(self, tilemap, movement=(0,0)):
        if self.walking:
            # Using the distance formula
            dis = pygame.math.Vector2(self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
            distance = dis.length()            
            if distance >= 30:
                angle = math.atan2(dis.y, dis.x)
                movement = (math.cos(angle) * self.speed, math.sin(angle) * self.speed)
                self.walking = True
            elif (abs(self.game.player.pos[1] - self.pos[1]) != 0):
                angle = math.atan2(dis.y, dis.x)
                movement = (0, math.sin(angle) * self.speed * 1.5)
                self.walking = True
                # get angle 
                angle = math.atan2(dis.y, dis.x)
                if not self.timer: # if self.timer = 0
                    if (self.flip and dis[0] < 0): # player is left of enemy, and enemy is looking left
                        self.timer = 60 # Set a cooldown timer for shooting (300 frames = 5 seconds)
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -2.5, 0])
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random())) # getting pos from projectiles in it's list, facing left
                    if (not self.flip and dis[0] > 0):
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 2.5, 0])
                        self.timer = 60  # Set a cooldown timer for shooting (300 frames = 5 seconds)
                        self.game.sfx['shoot'].play()
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random())) # facing right
        elif random.random() < 0.01: # 1 in every 6.1 seconds
            self.walking = random.randint(30, 120)
        
        # Reduce timer
        if self.timer > 0:
            self.timer -= 1
       
        super().update(tilemap, movement=movement)

        if movement[0] != 0 or movement[1] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()): # if enemy hitbox collides with player
                self.game.screenshake = max(16, self.game.screenshake)  # apply screenshake
                self.game.sfx['hit'].play()
                for i in range(30): # enemy death effect
                    # on death sparks
                    angle = random.random() * math.pi * 2 # random angle in a circle
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random())) 
                    # on death particles
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle * math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random())) # left
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random())) # right
                return True # [**]
                

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['bow'], True, False), (self.rect().centerx + 1 - self.game.assets['bow'].get_width() + 2 - offset[0], self.rect().centery - 8 - offset[1])) # renders the bow 
        else:
            surf.blit(self.game.assets['bow'], (self.rect().centerx - 1 - offset[0], self.rect().centery - 8 - offset[1]))

    

        
