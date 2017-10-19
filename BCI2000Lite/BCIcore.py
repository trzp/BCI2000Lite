#!user/bin/python
# -*-coding:utf-8-*-

#FileName: BCIcore.py
#Version: 1.0
#Author: Jingsheng Tang
#Date: 2017/8/9
#Email: mrtang@nudt.edu.cn
#Github: trzp

import thread
from core import core
from bcitypes import *
from threading import Event
import pygame
from pygame.locals import *
import time

try:    __INF__ = float('inf')
except: __INF__ = 0xFFFF


class BciCore(object):
    def __init__(self):
        #to be reset in the son class
        self.STATES = States()
        self.stimuli = {}
        self.expset = Expset()
        self.screen = None
        self.gui_fps = 120

        #other
        self.__phase_ev = Event()
        self.__stop_ev = Event()
        self.__eegsignal = EEG()
        self.__core = core(self.__phase_ev,self.__eegsignal,self.STATES,self.expset,self.__stop_ev)

    def init_screen(self,screen_siz=(0,0),screen_color=(0,0,0)):
        pygame.init()
        self.screen_color = screen_color
        if screen_siz == (0,0): self.screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN|pygame.DOUBLEBUF|pygame.HWSURFACE)
        else:  self.screen = pygame.display.set_mode(screen_siz,0,32)
        self.screen.fill(self.screen_color)
        self.__tick = pygame.time.Clock()

    def change_phase(self,phase):
        return self.__core.changephase(phase)

    def in_phase(self,phase):
        return self.__core.inphase(phase)

    @property
    def current_phase(self):
        return self.__core.currentphase

    def phase(self,name='',next='',duration=__INF__):   #define phases
        self.__core.addphase(name,next,duration)

    def Initialize(self):   #initialize the screen. arrange the stimuli. initialize the states.
        pass

    def Phase(self):
        pass

    def Frame(self): #called on ever screen frame
        pass

    def Transition(self,phase):
        pass

    def Process(self,sig):
        pass

    def __transition(self):
        print '\ntransition thread started!'
        while True:
            self.__phase_ev.wait()
            self.__phase_ev.clear()
            self.Transition(self.__core.currentphase)
            if self.__core.inphase('stop'):  break
        print '\ntransition thread ended!'

    def __process(self):
        clk = pygame.time.Clock()
        print '\nprocess thread started!'
        while True:
            self.__eegsignal.event.wait()
            self.__eegsignal.event.clear()
            self.Process(self.__eegsignal)
            if self.__core.inphase('stop'):break
        print '\nprocess thread ended!'

    def __updategui(self):
        if self.screen!=None:
            print '\nmain thread started!'
            END=0
            while True:
                self.Frame()
                self.screen.fill(self.screen_color)
                stis = sorted(self.stimuli.items(),key=lambda k:k[1].layer)
                for s in stis:  s[1].show()
                pygame.display.flip()
                self.__tick.tick_busy_loop(self.gui_fps)
                if self.__core.inphase('stop'):break

                evs = pygame.event.get()
                for e in evs:
                    if e.type == QUIT:  END=1
                    elif e.type == KEYDOWN:
                        if e.key == K_ESCAPE: END=1
                if END:break
            self.__core.changephase('stop')
            time.sleep(0.5)
            pygame.quit()
            print '\nmain thread ended!'
        else:
            while not self.__core.inphase('stop'):pass

    def StartRun(self):
        print '===========program started==================='
        print 'initializing...'
        self.Initialize()
        print 'initialized!'
        self.Phase()
        thread.start_new_thread(self.__process,())
        thread.start_new_thread(self.__transition,())
        self.__core.setDaemon(True)
        self.__core.start()
        self.__updategui()
        time.sleep(2)
        self.__stop_ev.wait()
        print '===========program finished=================='