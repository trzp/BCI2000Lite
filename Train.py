#!user/bin/python
# -*-coding:utf-8-*-

#FileName: main.py
#Version: 1.0
#Author: Jingsheng Tang
#Date: 2017/8/17
#Email: mrtang@nudt.edu.cn
#Github: trzp

import os,sys
root_path = os.path.split(__file__)[0]
os.sys.path.append(root_path+'/BCI2000Lite')
from BCIcore import *

os.sys.path.append(root_path+'/VisualStimuli')
from block import Block
from imagebox import Imagebox

os.sys.path.append(root_path+'/User/BCIrelate')
from BCIFunc import *
from P3Classification import P3Classification


from random import shuffle
import numpy as np
from copy import copy

import socket

class BciApplication(BciCore):
    def Initialize(self):
        self.STATES.state['code']=-1
        self.STATES.state['trial']=0
        self.STATES.state['Type']=-1 #type作为MATLAB的关键词，应当避免使用

        self.expset.experiment_name = 'smart car driving'
        self.expset.subject_name = 'TJS'
        self.expset.session = 1
        self.expset.run = 1
        self.expset.path = root_path + '/data'
        
        self.expset.Amp = 'signal_generator'#'actichamp'
        self.expset.amp_channels = 9
        self.expset.amp_samplingrate = 200
        self.expset.save_data = False

        signal_generator_waveform = 'sin'
        signal_generator_frequency = 20
        signal_generator_gain = 50

        self.em_sig = np.zeros((self.expset.amp_channels,50))
        self.em_code = -1*np.ones(50)
        self.signal = copy(self.em_sig)
        self.em_code = copy(self.em_code)
        self.FLG = 0

        self.Mode = 1
        self.p3result = 0
        if self.Mode:   self.P3Cla = P3Classification(root_path+'//param//'+'mud.mat',self.expset)

        tasklist = range(12)
        shuffle(tasklist)
        self.tasklist = tasklist
        self.current_task = ''
        self.currentbook = None
        self.currentindex = None
        self.res = 0
        
        self.cube_dim = (3,4)
        self.init_screen((1000,650))
        self.GUIsetup()
        self.gui_fps = 60

    def Phase(self):
        self.phase(name='start',       next='prompt',    duration=5)
        self.phase(name='prompt',      next='on',        duration=3)
        self.phase(name='on',          next='off',       duration=0.15)
        self.phase(name='off',         next='on',        duration=0.1)
        self.phase(name='preresult',   next='result',    duration=0.8)
        self.phase(name='result',      next='prompt',    duration=2)
        self.phase(name='stop')

    def StimAct(self,i,type):
        if type=='on':  self.stimuli['Flsh%d'%(i)].forecolor = (255,255,255,255)
        else:           self.stimuli['Flsh%d'%(i)].forecolor = (0,0,0,0)
        self.stimuli['Flsh%d'%(i)].reset()

    def Transition(self,phase):
        if phase == 'prompt':
            self.FLG = 1
            if len(self.tasklist)==0:   self.change_phase('stop')
            else:
                self.STATES.state['trial']+=1
                self.current_task = self.tasklist.pop()
                self.stimuli['prompt'].text = 'task: '+str(self.current_task)
                self.stimuli['prompt'].reset()

            self.cube, self.codebook0, self.codeindex0 = generate_RC_codebook(self.cube_dim,3)
            self.codebook = copy(self.codebook0)
            self.codeindex = copy(self.codeindex0)
        
        elif phase == 'on':
            if len(self.codeindex)==0:  self.change_phase('preresult')
            else:
                self.currentbook = self.codebook.pop()
                codeindex = self.codeindex.pop()
                self.STATES.state['code'] = codeindex
                if self.current_task in self.currentbook:
                    self.STATES.state['Type']=1
                else:
                    self.STATES.state['Type']=-1
                [self.StimAct(d,'on') for d in range(12) if d in self.currentbook]
                # [self.StimAct(d,'off') for d in range(12) if d not in self.currentbook]

        elif phase == 'off':
            self.STATES.state['code'] = -1
            [self.StimAct(d,'off') for d in range(12)]
        
        # elif phase == 'preresult':
            # [self.StimAct(d,'off') for d in range(12)]

        elif phase == 'result':
            if self.Mode == 0:
                self.stimuli['prompt'].text = ''
                self.stimuli['prompt'].reset()
            if self.Mode>0:
                res = self.P3Cla.rc_estimate(self.signal,self.stim_code,self.cube_dim)
                self.stimuli['prompt'].text = 'result: %s'%(str(self.cube[res[0],res[1]]),)
                self.stimuli['prompt'].reset()
                self.FLG = 0

    def Process(self,sig):
        if self.FLG:
            self.signal = np.hstack((self.signal,sig.eeg))
            self.stim_code = np.hstack((self.stim_code,sig.state['code']))
        else:
            self.signal = copy(self.em_sig)
            self.stim_code = copy(self.em_code)

    def GUIsetup(self):
        scrw,scrh = self.screen.get_size()
        
        self.stimuli['prompt'] = Block(self.screen,(300,100),(scrw/2,50),anchor='center',textcolor=(255,255,255),
                                       visible=True,text='task:',textsize=50,forecolor=(0,0,0,0))
        self.stimuli['prompt'].reset()

        ax = np.linspace(100,scrw-100,4).astype(np.int32)
        ay = np.linspace(150,scrh-100,3).astype(np.int32)

        indx = 0
        for y in ay:
            for x in ax:
                self.stimuli['Flsh%d'%(indx)] = Block(self.screen,(100,100),(x,y),anchor='center',
                                                   borderon=True,bordercolor=(255,0,255),visible=True,textsize=25,
                                                   layer=1,forecolor=(0,0,0,0),text=str(indx))
                self.stimuli['Flsh%d'%(indx)].reset()
                indx+=1

if __name__ == '__main__':
    app = BciApplication()
    app.StartRun()

