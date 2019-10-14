# music from https://opengameart.org/content/background-space-track
from direct.showbase.ShowBase import ShowBase
from panda3d.core import TextNode, TransparencyAttrib
from panda3d.core import *
from panda3d.core import LPoint3, LVector3
from direct.interval.SoundInterval import SoundInterval
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task
from math import sin, cos, pi
from random import randint, choice, random
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import Wait, Func
import sys
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import *
SPRITE_POS = 55
SCREEN_X = 20
SCREEN_Y = 15
TURN_RATE = 360
ACCELERATION = 10
MAX_VEL = 10
MAX_VEL_SQ = MAX_VEL ** 2
DEG_TO_RAD = pi / 180
AST_INIT_SCALE = 3
AST_SIZE_SCALE = .6
AST_MIN_SCALE = 1.1
def loadObject(tex=None, pos=LPoint3(0, 0), depth=SPRITE_POS, scale=1,
               transparency=True):
    obj = loader.loadModel("plane.bam")
    obj.reparentTo(render)
    obj.setPos(pos.getX(), depth, pos.getY())
    obj.setScale(scale)
    obj.setBin("unsorted", 0)
    obj.setDepthTest(False)
    if transparency:
        obj.setTransparency(TransparencyAttrib.MAlpha)
    if tex:
        tex = loader.loadTexture(tex)
        obj.setTexture(tex, 1)
    return obj
class AsteroidsDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        getModelPath().appendDirectory("data")
        self.AST_INIT_VEL = 0.6
        self.score = 0
        self.lives = 5
        self.BULLET_LIFE = 1.5
        self.BULLET_SPEED = 15
        self.BULLET_REPEAT = .2
        self.AST_VEL_SCALE = 1.2
        self.disableMouse()
        #self.ss = OnscreenText(text="0", parent=base.a2dTopLeft, pos=(0.07, -.06 * 1 - 0.1),fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.12)
        self.ss = OnscreenText(text="0",parent=base.a2dTopLeft,pos=(0.2,-0.1), scale=0.08,fg=(1, 1, 1, 1))
            # self.ll = OnscreenText(text="5", parent=base.a2dTopLeft, pos=(2.4, -1.76 * 1 - 0.1),fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=.12)
        self.ll = OnscreenText(text="5",parent=base.a2dTopLeft,pos=(2.5,-1.95), scale=0.08,fg=(1, 1, 1, 1))
        self.setBackgroundColor((0, 0, 0, 1))
        self.ship = loadObject("ship.png")
        self.setVelocity(self.ship, LVector3.zero())
        self.ship.hide()
        self.keys = {"turnLeft": 0, "turnRight": 0,
                     "accel": 0, "fire": 0}
        self.accept("escape", sys.exit)
        self.accept("arrow_left",     self.setKey, ["turnLeft", 1])
        self.accept("arrow_left-up",  self.setKey, ["turnLeft", 0])
        self.accept("arrow_right",    self.setKey, ["turnRight", 1])
        self.accept("arrow_right-up", self.setKey, ["turnRight", 0])
        self.accept("arrow_up",       self.setKey, ["accel", 1])
        self.accept("arrow_up-up",    self.setKey, ["accel", 0])
        self.accept("space",          self.setKey, ["fire", 1])
        self.gameon = 0
        self.gton = 0
        self.startgame()
        mySound = loader.loadSfx("music.wav")
        myInterval = SoundInterval(mySound, loop = 1)
        myInterval.loop()
    def startgame(self):
        self.nextBullet = 0.0
        self.bullets = []
        if self.gton == 0:
            self.gameTask = taskMgr.add(self.gameLoop, "gameLoop")
        # self.setVelocity(self.ship, LVector3.zero())
        self.ship.hide()
        self.setVelocity(self.ship, LVector3(0, 0, 0))
        # self.ship.show()
        Sequence(Wait(0),
            Func(self.ship.setR, 0),
            Func(self.ship.setX, 0),
            Func(self.ship.setZ, 0),
            Func(self.ship.show)).start()
            #Func(self.spawnAsteroids)).start()
        self.spawnAsteroids()
        self.gameon = 1
    def setKey(self, key, val):
        self.keys[key] = val
    def setVelocity(self, obj, val):
        obj.setPythonTag("velocity", val)
    def getVelocity(self, obj):
        return obj.getPythonTag("velocity")
    def setExpires(self, obj, val):
        obj.setPythonTag("expires", val)
    def getExpires(self, obj):
        return obj.getPythonTag("expires")
    def spawnAsteroids(self):
        self.alive = True
        self.asteroids = []
        for i in range(5):
            asteroid = loadObject("asteroid%d.png" % (randint(1, 3)),
                                  scale=AST_INIT_SCALE)
            self.asteroids.append(asteroid)
            asteroid.setX(choice(tuple(range(-SCREEN_X, -5)) + tuple(range(5, SCREEN_X))))
            asteroid.setZ(choice(tuple(range(-SCREEN_Y, -5)) + tuple(range(5, SCREEN_Y))))
            heading = random() * 2 * pi
            v = LVector3(sin(heading), 0, cos(heading)) * self.AST_INIT_VEL
            self.setVelocity(self.asteroids[i], v)
    def gameLoop(self, task):
        self.gton = 1
        dt = globalClock.getDt()
        if not self.alive:
            return Task.cont
        self.updateShip(dt)
        self.ss.setText(str(self.score))
        self.ll.setText(str(self.lives))
        if self.keys["fire"] and task.time > self.nextBullet:
            self.fire(task.time)
            self.nextBullet = task.time + self.BULLET_REPEAT
        self.keys["fire"] = 0
        for obj in self.asteroids:
            self.updatePos(obj, dt)
        newBulletArray = []
        for obj in self.bullets:
            self.updatePos(obj, dt)
            #self.updatePosnowarp(obj, dt)
            if self.getExpires(obj) > task.time:
                newBulletArray.append(obj)
            else:
                obj.removeNode()
        self.bullets = newBulletArray
        for bullet in self.bullets:
            for i in range(len(self.asteroids) - 1, -1, -1):
                asteroid = self.asteroids[i]
                if ((bullet.getPos() - asteroid.getPos()).lengthSquared() <
                    (((bullet.getScale().getX() + asteroid.getScale().getX())
                      * .5) ** 2)):
                    self.setExpires(bullet, 0)
                    self.asteroidHit(i)
        shipSize = self.ship.getScale().getX()
        for ast in self.asteroids:
            if ((self.ship.getPos() - ast.getPos()).lengthSquared() <
                    (((shipSize + ast.getScale().getX()) * .5) ** 2)):
                if self.lives is 0:
                   self.alive = False
                   for i in self.asteroids + self.bullets:
                       i.removeNode()
                   self.bullets = []
                   self.ship.hide()
                   self.score = 0
                   self.AST_INIT_VEL = 0.6
                   self.AST_VEL_SCALE = 1.8
                   self.lives = 5
                   self.setVelocity(self.ship, LVector3(0, 0, 0))
                   self.go = OnscreenText(text="Game Over", parent=base.a2dTopLeft, pos=(0.5, -1 * 1 ),fg=(1, 1, 1, 1), align=TextNode.ALeft, shadow=(0, 0, 0, 0.5), scale=0.3)
                   self.BULLET_LIFE = 1.5
                   self.BULLET_SPEED = 15
                   self.BULLET_REPEAT = .2
                   self.AST_VEL_SCALE = 1.2
                   self.gameon = 0
                   myTask = taskMgr.doMethodLater(2, self.hidego, "tickTask")
                   Sequence(Wait(2),
                    Func(self.ship.setR, 0),
                    Func(self.ship.setX, 0),
                    Func(self.ship.setZ, 0),
                    Func(self.ship.show),
                    Func(self.spawnAsteroids)).start()
                else:
                    self.alive = False
                    for i in self.asteroids + self.bullets:
                      i.removeNode()
                    self.bullets = []
                    self.ship.hide()
                    self.setVelocity(self.ship, LVector3(0, 0, 0))
                    Sequence(Wait(2),
                            Func(self.ship.setR, 0),
                            Func(self.ship.setX, 0),
                            Func(self.ship.setZ, 0),
                            Func(self.ship.show),
                            Func(self.spawnAsteroids)).start()
                    self.lives = (self.lives) - 1
                return Task.cont
        if len(self.asteroids) == 0:
            self.spawnAsteroids()
        return Task.cont
    def updatePos(self, obj, dt):
        vel = self.getVelocity(obj)
        newPos = obj.getPos() + (vel * dt)
        radius = .5 * obj.getScale().getX()
        if newPos.getX() - radius > SCREEN_X:
            newPos.setX(-SCREEN_X)
        elif newPos.getX() + radius < -SCREEN_X:
            newPos.setX(SCREEN_X)
        if newPos.getZ() - radius > SCREEN_Y:
            newPos.setZ(-SCREEN_Y)
        elif newPos.getZ() + radius < -SCREEN_Y:
            newPos.setZ(SCREEN_Y)
        obj.setPos(newPos)
    def updatePosnowarp(self, obj, dt):
        vel = self.getVelocity(obj)
        newPos = obj.getPos() + (vel * dt)
        radius = .5 * obj.getScale().getX()
        obj.setPos(newPos)
    def asteroidHit(self, index):
        if self.asteroids[index].getScale().getX() <= AST_MIN_SCALE:
            self.asteroids[index].removeNode()
            mySound2 = base.loader.loadSfx("hit.wav")
            mySound2.play()
            del self.asteroids[index]
        else:
            asteroid = self.asteroids[index]
            newScale = asteroid.getScale().getX() * AST_SIZE_SCALE
            asteroid.setScale(newScale)
            vel = self.getVelocity(asteroid)
            speed = vel.length() * self.AST_VEL_SCALE
            vel.normalize()
            vel = LVector3(0, 1, 0).cross(vel)
            vel *= speed
            self.setVelocity(asteroid, vel)
            newAst = loadObject(scale=newScale)
            self.setVelocity(newAst, vel * -1)
            newAst.setPos(asteroid.getPos())
            newAst.setTexture(asteroid.getTexture(), 1)
            self.asteroids.append(newAst)
            self.score = (self.score) + 50
            self.BULLET_SPEED = (self.BULLET_SPEED) + 1
            #  self.BULLET_LIFE = (self.BULLET_LIFE) + 0.05
            self.BULLET_REPEAT = (self.BULLET_REPEAT) - 0.003
            self.AST_INIT_VEL = (self.AST_INIT_VEL) + 0.1
            self.AST_VEL_SCALE = (self.AST_VEL_SCALE) + 0.005
            mySound2 = base.loader.loadSfx("hit.wav")
            mySound2.play()
    def updateShip(self, dt):
        heading = self.ship.getR()
        if self.keys["turnRight"]:
            heading += dt * TURN_RATE
            self.ship.setR(heading % 360)
        elif self.keys["turnLeft"]:
            heading -= dt * TURN_RATE
            self.ship.setR(heading % 360)
        if self.keys["accel"]:
            heading_rad = DEG_TO_RAD * heading
            newVel = LVector3(sin(heading_rad), 0, cos(heading_rad)) * ACCELERATION * dt
            newVel += self.getVelocity(self.ship)
            if newVel.lengthSquared() > MAX_VEL_SQ:
                newVel.normalize()
                newVel *= MAX_VEL
            self.setVelocity(self.ship, newVel)
        self.updatePos(self.ship, dt)
    def fire(self, time):
        direction = DEG_TO_RAD * self.ship.getR()
        pos = self.ship.getPos()
        bullet = loadObject("bullet.png", scale=0.2)
        bullet.setPos(pos)
        vel = (self.getVelocity(self.ship) +
               (LVector3(sin(direction), 0, cos(direction)) *
                self.BULLET_SPEED))
        self.setVelocity(bullet, vel)
        self.setExpires(bullet, time + self.BULLET_LIFE)
        self.bullets.append(bullet)
        mySound1 = base.loader.loadSfx("fire.wav")
        mySound1.play()
    def hidego(self,task):
        self.go.hide()
demo = AsteroidsDemo()
demo.run()
