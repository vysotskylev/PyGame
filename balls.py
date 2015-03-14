#!/usr/bin/env python
# coding: utf

import pygame
import random
import math

SIZE = 640, 480

def plus(a): return a[0] + a[1]

def intn(*arg):
    return map(int,arg)

def binop(op, a, b):
    return map(op, zip(a,b))

def dot(a,b): return a[0]*b[0] + a[1]*b[1]
def normalize(v):
    l = v[0] ** 2 + v[1] ** 2
    if l < 0.00001:
        return v
    l = math.sqrt(l)
    return (v[0] / l, v[1] / l)

def Init(sz):
    '''Turn PyGame on'''
    global screen, screenrect
    pygame.init()
    screen = pygame.display.set_mode(sz)
    screenrect = screen.get_rect()

class GameMode:
    '''Basic game mode class'''
    def __init__(self):
        self.background = pygame.Color("black")

    def Events(self,event):
        '''Event parser'''
        pass

    def Draw(self, screen):
        screen.fill(self.background)

    def Logic(self, screen):
        '''What to calculate'''
        pass

    def Leave(self):
        '''What to do when leaving this mode'''
        pass

    def Init(self):
        '''What to do when entering this mode'''
        pass

class Ball:
    '''Simple ball class'''

    def __init__(self, filename, pos = (0.0, 0.0), speed = (0.0, 0.0), gravity = 0.0):
        '''Create a ball from image'''
        self.fname = filename
        self.surface = pygame.image.load(filename)
        self.rect = self.surface.get_rect()
        self.speed = speed
        self.pos = pos
        self.oldpos = pos
        self.active = True
        self.gravity = gravity

    def draw(self, surface):
        surface.blit(self.surface, self.rect)

    def action(self):
        '''Proceed some action'''
        if self.active:
            self.oldpos = self.pos
            self.pos = self.pos[0]+self.speed[0], self.pos[1]+self.speed[1]

    def logic(self, surface):
        x,y = self.pos
        dx, dy = self.speed
        if x < self.rect.width/2:
            x = self.rect.width/2
            dx = -dx
        elif x > surface.get_width() - self.rect.width/2:
            x = surface.get_width() - self.rect.width/2
            dx = -dx
        if y < self.rect.height/2:
            y = self.rect.height/2
            dy = -dy
        elif y > surface.get_height() - self.rect.height/2:
            y = surface.get_height() - self.rect.height/2
            dy = -dy
        self.pos = x,y
        self.speed = (dx,dy + self.gravity)
        self.rect.center = intn(*self.pos)
class RotatingScaleBall(Ball):
    def __init__(self, filename, pos = (0.0, 0.0), scale = 1.0, speed = (0.0, 0.0), rotSpeed = 0.0, gravity = 0.0):
        Ball.__init__(self, filename, pos, speed, gravity)
        self.rect.w, self.rect.h = self.rect.w * scale, self.rect.h * scale
        self.rect.topleft = self.pos
        self.rotSpeed = rotSpeed
        self.angle = 0.0
        self.scale = scale
    def action(self):
        Ball.action(self)
        if self.active:
            self.angle += self.rotSpeed
    def draw(self, surface):
        newSurf = pygame.transform.rotozoom(self.surface, self.angle,self.scale)
        newRect = newSurf.get_rect()
        newRect.center = self.rect.center
        surface.blit(newSurf, newRect)

class MaskedBall(RotatingScaleBall):
    def __init__(self, filename, pos = (0.0, 0.0), scale = 1.0, speed = (0.0, 0.0), rotSpeed = 0.0, gravity = 0.0):
        RotatingScaleBall.__init__(self, filename, pos, scale, speed, rotSpeed, gravity)
        self.mask = pygame.mask.from_surface(self.surface).scale(self.rect.size)
   
    def get_collision_direction(self, other):
        x, y = other.rect.left - self.rect.left, other.rect.top - self.rect.top
        othermask = other.mask
        dx = self.mask.overlap_area(othermask,(x+1,y)) - self.mask.overlap_area(othermask,(x-1,y))
        dy = self.mask.overlap_area(othermask,(x,y+1)) - self.mask.overlap_area(othermask,(x,y-1))
        return dx, dy

class MassiveBall(MaskedBall):
    density = 0.1
    @staticmethod
    def get_speeds_after_collision(b1, b2, colDir):
        # special convinient coordinate system...
        X = normalize(colDir)
        Y = (-X[1], X[0])
        # .. and casting to it ...
        v1 = (dot(b1.speed, X), dot(b1.speed, Y))
        v2 = (dot(b2.speed, X), dot(b2.speed, Y))
        # .. calculating new speeds ...
        dpMag = 2 * (v2[0] - v1[0]) / (1.0/b1.mass + 1.0/b2.mass)
        w1 = (v1[0] + dpMag / b1.mass, v1[1])
        w2 = (v2[0] - dpMag / b2.mass, v2[1])
        #... and casting back...
        sp1 = (X[0] * w1[0] + Y[0] * w1[1], X[1] * w1[0] + Y[1] *w1[1])
        sp2 = (X[0] * w2[0] + Y[0] * w2[1], X[1] * w2[0] + Y[1] *w2[1])
        return (sp1, sp2)


    def __init__(self, filename, pos = (0.0, 0.0), scale = 1.0, speed = (0.0, 0.0), rotSpeed = 0.0, gravity = 0.0):
        MaskedBall.__init__(self, filename, pos, scale, speed, rotSpeed, gravity)
        self.mass = scale ** 2 * MassiveBall.density
class Universe:
    '''Game universe'''

    def __init__(self, msec, tickevent = pygame.USEREVENT):
        '''Run a universe with msec tick'''
        self.msec = msec
        self.tickevent = tickevent

    def Start(self):
        '''Start running'''
        pygame.time.set_timer(self.tickevent, self.msec)

    def Finish(self):
        '''Shut down an universe'''
        pygame.time.set_timer(self.tickevent, 0)

class GameWithObjects(GameMode):

    def __init__(self, objects=[]):
        GameMode.__init__(self)
        self.objects = objects

    def locate(self, pos):
        return [obj for obj in self.objects if obj.rect.collidepoint(pos)]

    def Events(self, event):
        GameMode.Events(self, event)
        if event.type == Game.tickevent:
            for obj in self.objects:
                obj.action()

    def Logic(self, surface):
        GameMode.Logic(self, surface)
        for obj in self.objects:
            obj.logic(surface)
        for i in xrange(len(self.objects)):
            obj1 = self.objects[i]
            for j in xrange(i + 1, len(self.objects)):
                obj2 = self.objects[j]
                dx, dy = obj1.get_collision_direction(obj2)
                if dx or dy:
                    obj1.pos = obj1.oldpos
                    obj2.pos = obj2.oldpos
                    obj1.speed, obj2.speed = MassiveBall.get_speeds_after_collision(obj1, obj2, (dx, dy))
    def Draw(self, surface):
        GameMode.Draw(self, surface)
        for obj in self.objects:
            obj.draw(surface)

class GameWithDnD(GameWithObjects):
    def __init__(self, *argp, **argn):
        GameWithObjects.__init__(self, *argp, **argn)
        self.oldpos = 0,0
        self.drag = None

    def Events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = self.locate(event.pos)
            if click:
                self.drag = click[0]
                self.drag.active = False
                self.oldpos = event.pos
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                if self.drag:
                    self.drag.pos = event.pos
                    self.drag.speed = event.rel
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag is not None:
            self.drag.active = True
            self.drag = None
        GameWithObjects.Events(self, event)

Init(SIZE)
Game = Universe(25)

Run = GameWithDnD()
for i in xrange(3):
    x, y = random.randrange(screenrect.w), random.randrange(screenrect.h)
    dx, dy = 1+random.random()*5, 1+random.random()*5
    Run.objects.append(MassiveBall("ball.gif",(x,y), random.random() + 0.6, (dx,dy), 1, 0.25))

Game.Start()
Run.Init()
again = True
while again:
    event = pygame.event.wait()
    if event.type == pygame.QUIT:
        again = False
    Run.Events(event)
    Run.Logic(screen)
    Run.Draw(screen)
    pygame.display.flip()
Game.Finish()
pygame.quit()
