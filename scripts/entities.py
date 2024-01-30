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


    def render(self, surf, images, rotation, offset={0,0}, spread=1):
        '''
        partly overriding rendering for dashing
        '''
        for i, img in enumerate(images):
            rotated_img = pygame.transform.rotate(img, rotation)
            surf.blit(rotated_img, (self.pos[0] - rotated_img.get_width()  - offset[0] + self.anim_offset[0] // 2, self.pos[1] - rotated_img.get_height()  - offset[0] + self.anim_offset[0] // 2 - i * spread))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates player entity
        (game, position, size)
        '''
        super().__init__(game,'player', pos, size)
        self.speed = 2.2

    def update(self, tilemap, movement=(0,0)):
        '''
        updates players animations depending on movement
        '''
        super().update(tilemap, movement=movement)
        self.set_action('idle')



        trueWidth =  self.game.screen.get_width() + 30
        trueHeight = self.game.screen.get_height() + 20

        # Player boundary
        if self.pos[1] >= trueHeight:
            self.game.dead += 1
            self.pos[1] = trueHeight
        if self.pos[0] < 50:
            self.game.dead += 1
            self.pos[0] = 50
        if self.pos[1] < 60:
            self.game.dead += 1
            self.pos[1] = 60

        if self.pos[0] > trueWidth:
            self.game.dead += 1
            self.pos[0] = trueWidth 

    def rect(self):
        '''
        creates a rectangle at the entitiies current postion
        '''
        return pygame.Rect(self.pos[0] - 33, self.pos[1] - 50, self.size[0], self.size[1])

 
            

class Enemies(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates the enemies
        (game, position: tuple, size)
        '''
        super().__init__(game, 'enemy', pos, size)
    
    def update(self, tilemap, movement=(0,0)):
        super().update(tilemap, movement=movement)

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
        
    def rect(self):
        '''
        creates a rectangle at the entitiies current postion
        '''
        return pygame.Rect(self.pos[0] - 30, self.pos[1] - 40, self.size[0], self.size[1])
    
    def render(self, surf, images, rotation, offset={0,0}, spread=1):
        super().render(surf, images, rotation=rotation, offset=offset, spread=1)


class Boss(PhysicsEntity):
    def __init__(self, game, pos, size):
        '''
        instantiates the enemies
        (game, position: tuple, size)
        '''
        super().__init__(game, 'boss', pos, size)
    
    def update(self, tilemap, movement=(0,0)):
        super().update(tilemap, movement=movement)

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
        
    def rect(self):
        '''
        creates a rectangle at the entitiies current postion
        '''
        return pygame.Rect(self.pos[0] - 30, self.pos[1] - 40, self.size[0], self.size[1])
    
    def render(self, surf, images, rotation, offset={0,0}, spread=1):
        super().render(surf, images, rotation=rotation, offset=offset, spread=1)