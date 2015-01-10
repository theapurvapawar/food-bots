from pygamehelper import *
from pygame import *
from pygame.locals import *
from vec2d import *
from math import e, pi, cos, sin, sqrt, exp
from random import uniform, randint, normalvariate
import pygame.gfxdraw


#simulation container window
WIDTH = 800
HEIGHT = 600

BOTCOUNT = 15 #initial bot count

#brain
BRAIN_SIZE = 20
BRAIN_DENSITY = 7 #number of synapses per neuron

#mutation
MUT_RATE = 0.1 #probability of mutation
MUT_SEV = 0.3 #severety of mutation

#bot characteristics
BOT_RADIUS = 15 #radius of bot

#bot health
HEALTH = 1
MAX_AGE = 150 #max bot age in seconds

#bot eyes
EYE_SEP = 0.6 #seperation of eyes in radians
EYE_SENS = 0.0003 #sensitivity of eye (Lower value = more sensitive)
EYE_MULT = 0.7 #linear multiplier on strengh of eye

#bot speed
SPEED = 4
BOOST_COST = 0.001 #how much does use of boost affect health

#food
FOOD_LOSS = 0.001
FOOD_ADD_FREQ = 5
FOOD_LIMIT = 80
FOOD_GAIN = 0.7

#replication
REP_THR = 3


############Do not change anything below this############

FPS=40


#colors
BLACK = (  0,   0,   0)
GRAY  = (128, 128, 128)
WHITE = (255, 255, 255)

RED     = (255,   0,   0)
GREEN   = (  0, 255,   0)
BLUE    = (  0,   0, 255)
CYAN    = (  0, 255, 255)
MAGENTA = (255,   0, 255)
YELLOW  = (255, 255,   0)
BROWN   = (200,  50,   0)

class Brain:
    def __init__(self):
        #1D array of neuron activities
        self.act = []
        for i in range(BRAIN_SIZE):
            self.act.append(0)
            
        #2D array of synapse weights and indexes
        self.weight = [[0 for x in xrange(BRAIN_DENSITY)]for x in range(BRAIN_SIZE)]
        self.index = [[0 for x in xrange(BRAIN_DENSITY)] for x in range(BRAIN_SIZE)]
        for i in range(BRAIN_SIZE):
            for j in range(BRAIN_DENSITY):
                self.weight[i][j] = uniform(-1.2, 1.2)
                self.index[i][j] = randint(0, BRAIN_SIZE-1)
                                                   
    #feed inputs to neurons and take output
    def tick(self, l_eye, r_eye):
        #set inputs
        self.act[0] = l_eye
        self.act[1] = r_eye

        #set some bias neutrons to be always on
        self.act[3] = 1
        self.act[4] = 1
        self.act[9] = 1
        self.act[10] = 1        

        for i in range(BRAIN_SIZE):
            a = 0
            for j in range(BRAIN_DENSITY):
                a = a+self.weight[i][j]*self.act[self.index[i][j]]
            self.act[i] = 1/(1+exp(-a)) #pass through sigmoid

        res0 = self.act[BRAIN_SIZE-1]-0.6 #controls direction
        res1 = self.act[BRAIN_SIZE-2] #controls boost
        res2 = self.act[BRAIN_SIZE-3] #controls speed

        return res0, res1, res2

    #mutate brain of child during reproduction
    def mutateFrom(self, brain):
        #lossy copy of bain structure
        for i in range(BRAIN_SIZE):
            for j in range(BRAIN_DENSITY):

                m = brain.weight[i][j]
                if uniform(0, 1)<MUT_RATE:
                    m = m+normalvariate(0, MUT_SEV)
                self.weight[i][j] = m

                m = brain.index[i][j]
                if uniform(0, 1)<MUT_RATE:
                    m = randint(0, BRAIN_SIZE-1)
                self.index[i][j] = m

class Agent:
    def __init__(self):
        #position and direction
        self.pos = vec2d(uniform(0, WIDTH), uniform(0, HEIGHT))
        self.dir = uniform(0, 2*pi)
        self.rad = BOT_RADIUS
        
        #sensors
        self.l_eye = 0
        self.r_eye = 0

        #others
        self.speed = SPEED
        self.boost = 0.1 #speed variance
        self.health = HEALTH
        self.rep = 0 #replication counter
        self.selected = False
        self.children=0

        #attributes
        self.gen=0
        self.age=0
        self.temp=0
        self.color=(0, 0, 0)
        self.l_eye_color=GRAY
        self.r_eye_color=GRAY
        self.eye_rad=0#self.rad/3
        self.eye_len=0#self.rad+1

        self.asx1, self.asy1, self.asx2, self.asy2 = 0, 0, 0, 0
        self.ex1, self.ey1, self.ex2, self.ey2 = 0, 0, 0, 0
        self.ax1, self.ay1, self.ax2, self.ay2 = 0, 0, 0, 0

        #brain
        self.brain = Brain()

    def updateSize(self):

        self.eye_rad=self.rad/3
        self.eye_len=self.rad+1

        self.a1 = -EYE_SEP +self.dir
        self.a2 = EYE_SEP +self.dir

        #first compute eye position
        self.ex1 = int(cos(self.a1)*self.rad+1 + self.pos.x)
        self.ey1 = int(sin(self.a1)*self.rad+1 + self.pos.y)
        self.ex2 = int(cos(self.a2)*self.rad+1 + self.pos.x)
        self.ey2 = int(sin(self.a2)*self.rad+1 + self.pos.y)

        #next compute antenna start position
        self.asx1 = int(cos(self.a1)*self.rad + self.pos.x)
        self.asy1 = int(sin(self.a1)*self.rad + self.pos.y)
        self.asx2 = int(cos(self.a2)*self.rad + self.pos.x)
        self.asy2 = int(sin(self.a2)*self.rad + self.pos.y)

        #then compute antenna end position
        self.ax1 = int(cos(self.a1)*self.rad*2 + self.pos.x)
        self.ay1 = int(sin(self.a1)*self.rad*2 + self.pos.y)
        self.ax2 = int(cos(self.a2)*self.rad*2 + self.pos.x)
        self.ay2 = int(sin(self.a2)*self.rad*2 + self.pos.y)

    def updateColor(self):
        #update body color
        #self.color=(  0, 255*self.health, 255*self.health)
        if self.gen%10==0: self.color=BLACK
        if self.gen%10==1: self.color=GRAY
        if self.gen%10==2: self.color=RED
        if self.gen%10==3: self.color=GREEN
        if self.gen%10==4: self.color=BLUE
        if self.gen%10==5: self.color=CYAN
        if self.gen%10==6: self.color=YELLOW
        if self.gen%10==7: self.color=MAGENTA
        if self.gen%10==8: self.color=BROWN
        if self.gen%10==9: self.color=WHITE
            

        #update eye color
        self.l_eye_color=(50+205*(self.l_eye), 100, 100)
        self.r_eye_color=(50+205*(self.r_eye), 100, 100)

class Starter(PygameHelper):
    def __init__(self):
        self.w, self.h = WIDTH, HEIGHT
        PygameHelper.__init__(self, size=(self.w, self.h), fill=((255,255,255)))

        self.counter=0
        self.agents = []
        self.food = []

        self.drawStats = True
        self.drawFood = True
        self.openSystem = False

        print "Key Map:"
        print "ESC: Quit"
        print "D: Bot Stats - ON/OFF"
        print "F: Draw Food - ON/OFF"
        print "O: Add more bots automatically if there are few left"
        #print Date()

        for i in range(BOTCOUNT):
            new_agent = Agent()
            self.agents.append(new_agent)
        
    def update(self):
        self.counter = self.counter+1
        self.time = int(self.counter/FPS)
        
        pygame.display.set_caption("FPS: %i BOT: %i (%i seconds)" % (self.clock.get_fps(),len(self.agents), self.time))

        if self.openSystem == True:
            #spawn agents if there are too few left
            if len(self.agents)<8:
                new_agent = Agent()
                self.agents.append(new_agent)
        
        for a in self.agents:
            #move agent
            vel = vec2d((a.boost+a.speed)*cos(a.dir), (a.boost+a.speed)*sin(a.dir))
            a.pos.x = a.pos.x + vel.x
            a.pos.y = a.pos.y + vel.y

            #enforce boundary conditions: wrap around container
            if a.pos.x<0: a.pos.x=self.w
            if a.pos.x>self.w: a.pos.x=0
            if a.pos.y<0: a.pos.y=self.h
            if a.pos.y>self.h: a.pos.y=0

            #update agent size
            a.updateSize()

            if self.counter%FPS==0:
                if a.rad<=BOT_RADIUS:
                    a.rad = a.rad+1

            #change color
            a.updateColor()

            #update age and kill above max age
            if self.counter%FPS==0:
                a.age=a.age+1
            if a.age>=MAX_AGE:
                self.agents.remove(a)

            #agent gets hungry
            a.health = a.health - FOOD_LOSS
            a.health = a.health - BOOST_COST*a.boost
            if a.health<0: self.agents.remove(a) #kill if health goes below zero
           
            
        #collision detection and resolution
        for a in self.agents:
            for b in self.agents:
                if a==b: continue
                d = sqrt(pow(a.pos.x-b.pos.x,2) + pow(a.pos.y-b.pos.y,2))
                overlap = a.rad+b.rad-d
                if (overlap>0):
                    if(d>1):
                        #one agent pushes another propotional to his boost. Higher boost wins
                        aggression = b.boost/(a.boost+b.boost)
                        if a.boost<0.01:
                            if b.boost<0.01:
                                aggression = 0.5
                        ff2 = (overlap*aggression)/d
                        ff1 = (overlap*(1-aggression))/d
                        b.pos.x = b.pos.x + (b.pos.x-a.pos.x)*ff2
                        b.pos.y = b.pos.y + (b.pos.y-a.pos.y)*ff2
                        a.pos.x = a.pos.x - (b.pos.x-a.pos.x)*ff1
                        a.pos.y = a.pos.y - (b.pos.x-a.pos.x)*ff1


        #spawn more food, maybe
        if self.counter%FOOD_ADD_FREQ==0:
            if len(self.food)<FOOD_LIMIT:
                f = vec2d(uniform(0,self.w), uniform(0,self.h))
                self.food.append(f)

        #check if any agent ate food
        #also compute input to sense
        for a in self.agents:
            a.l_eye, a.r_eye = 0, 0

            for f in self.food:
                d2=sqrt(pow(a.pos.x-f.x,2)+pow(a.pos.y-f.y,2))
                if d2<a.rad:
                    a.rep = a.rep + FOOD_GAIN
                    a.health = a.health + FOOD_GAIN
                    if a.health>1: a.health=1
                    self.food.remove(f)

                if d2<a.rad*20: #if food within visible range
                    #compute position of both eyes in world co-ordinates
                    x1 = a.pos.x + a.eye_len*cos(a.dir-EYE_SEP)
                    y1 = a.pos.y + a.eye_len*cos(a.dir-EYE_SEP)
                    x2 = a.pos.x + a.eye_len*cos(a.dir+EYE_SEP)
                    y2 = a.pos.y + a.eye_len*cos(a.dir+EYE_SEP)

                    a.l_eye = a.l_eye + EYE_MULT*exp(-EYE_SENS*(pow(x1-f.x,2) + pow(y1-f.y,2)))
                    a.r_eye = a.r_eye + EYE_MULT*exp(-EYE_SENS*(pow(x2-f.x,2) + pow(y2-f.y,2)))

                    if a.l_eye>1: a.l_eye=1
                    if a.l_eye<0: a.l_eye=0
                    if a.r_eye>1: a.r_eye=1
                    if a.r_eye<0: a.r_eye=0                    

        #feed forward the brain from senses/input to the output
        for a in self.agents:
            res = a.brain.tick(a.l_eye, a.r_eye)
            
            #apply output neuron 0: control turning (cap to max 0.3 rotation)
            des = res[0]
            #print des
            if des>0.8: des=0.8
            if des<-0.8: des=-0.8
            a.dir = a.dir + des 

            #wrap direction around to keep it in range of 0-2pi
            if a.dir>2*pi: a.dir = a.dir - 2*pi
            if a.dir<0: a.dir = a.dir + 2*pi

            #apply output neuron 1: control boost
            des = res[1]
            if des>0: a.boost = des
            else: a.boost = 0

            #apply output neuron 2: control speed
            #des = res[2]
            #if des>1 : des = 1
            #if des<0 : des = 0
            #a.speed = SPEED/2 + (SPEED/2)*des

        #hande reproduction
        for a in self.agents:
            if a.rep>REP_THR:
                #this agent reproduces
                if a.children < 2:
                    a.rep=0
                    anew = Agent()
                    anew.pos = vec2d(a.pos.x+uniform(-a.rad*2, a.rad*2), a.pos.y+uniform(-a.rad*2, a.rad*2))
                    anew.brain.mutateFrom(a.brain)
                    anew.rad=5
                    anew.gen=a.gen+1
                    self.agents.append(anew)
                    a.children = a.children + 1
    

            
    def keyUp(self, key):
        if key==K_d:
            if self.drawStats == True:
                self.drawStats = False
                print "Bot Stats - OFF"
            else:
                self.drawStats = True
                print "Bot Stats - ON"

        if key==K_f:
            if self.drawFood == True:
                self.drawFood = False
                print "Draw Food - OFF"
            else:
                self.drawFood = True
                print "Draw Food - ON"

        if key==K_o:
            if self.openSystem == False:
                self.openSystem = True
                print "System is open - More bots will be added if there are too few left"
            else:
                self.openSystem = False
                print "System is NOT open"
        
    def mouseUp(self, button, pos):
        pass
        
    def mouseMotion(self, buttons, pos, rel):
        pass
        
    def draw(self):
        self.screen.fill(WHITE)
        basicfont = pygame.font.SysFont(None,20)
        
        if self.drawFood == True:
            #draw food
            for f in self.food:
                pygame.gfxdraw.filled_circle(self.screen, f.inttup()[0], f.inttup()[1], 4, BROWN)


        #draw all agents
        for a in self.agents:                            
                       
            #draw agent body and outline
            pygame.gfxdraw.filled_circle(self.screen, a.pos.inttup()[0], a.pos.inttup()[1], a.rad, BLACK)
            pygame.gfxdraw.filled_circle(self.screen, a.pos.inttup()[0], a.pos.inttup()[1], a.rad-1, a.color)

            #draw agent eyes
            pygame.gfxdraw.filled_circle(self.screen, a.ex1, a.ey1, a.eye_rad, a.l_eye_color)
            pygame.gfxdraw.filled_circle(self.screen, a.ex2, a.ey2, a.eye_rad, a.r_eye_color)

            #draw agent antenna
            pygame.gfxdraw.line(self.screen, a.asx1, a.asy1, a.ax1, a.ay1, BLACK)
            pygame.gfxdraw.line(self.screen, a.asx2, a.asy2, a.ax2, a.ay2, BLACK)

            if self.drawStats==True:
                #draw health bar
                pygame.draw.rect(self.screen, BLACK, (a.pos.x+30, a.pos.y-a.rad,7,20))
                pygame.draw.rect(self.screen, GREEN, (a.pos.x+31, a.pos.y-a.rad+1,5,20*a.health))

                #draw generation number
                label = basicfont.render(str(a.gen), 1, BLACK)
                self.screen.blit(label, (a.pos.x+30, a.pos.y+5))
s = Starter()
s.mainLoop(BOTCOUNT,FPS)
