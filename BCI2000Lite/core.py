#!user/bin/python
# -*-coding:utf-8-*-

#FileName: core.py
#Version: 1.0
#Author: Jingsheng Tang
#Date: 2017/8/10
#Email: mrtang@nudt.edu.cn
#Git: trzp

import win32api,win32con
import scipy.io
import numpy as np
import time
import threading

from ampclient import AmpClient,SigGen
from storage import Storage
from bcitypes import *

try:    __INF__ = float('inf')
except: __INF__ = 0xFFFF

class core(threading.Thread):
    def __init__(self,phase_ev,sig,bci_sts,expset,stp):
        self.stp = stp
        self.phase_ev = phase_ev
        self.sig = sig
        self.bci_sts = bci_sts
        self.expset = expset

        self.currentphase = 'start'
        self.PHASES = {'start':{'next':'','duration':__INF__},'stop':0}
        self.param = EEGparam()
        threading.Thread.__init__(self)

    def addphase(self,name='',next='',duration=__INF__):
        self.PHASES[name]={'next':next,'duration':duration}

    def inphase(self,phase):
        return phase==self.currentphase

    def changephase(self,phase):
        if self.PHASES.has_key(phase):
            self.currentphase=phase
            self.__clk = time.clock()
            self.phase_ev.set()
        else:
            raise IOError,'no phase: %s found!'%(phase)

    def run(self):
        print '\ncore thread started!'
        stskeys = self.bci_sts.state.keys()
        stsnum = len(stskeys)

        if self.expset.Amp == 'actichamp':  self.amp = AmpClient()
        elif self.expset.Amp == 'signal_generator': self.amp = SigGen(self.expset)
        else:raise IndexError,'unrecognized amplifier: ' + self.expset.Amp

        #param cheack
        if self.amp.param.eegchannels != self.expset.amp_channels or\
            self.amp.param.samplingrate != self.expset.amp_samplingrate:
            raise IndexError,'dismatch between amplifier and experiment set!'

        self.amp.freshind()
        if self.expset.save_data:   self.store = Storage(self.expset,self.amp.param,stskeys)
        temsts = np.zeros((stsnum,400000),dtype=np.float64)
        while not self.amp.getdata()[0]:  pass
        indx = 0

        self.__clk = time.clock()
        self.phase_ev.set()

        while True:
            clk = time.clock()

            for i in range(stsnum):
                temsts[i,indx]=self.bci_sts.state[stskeys[i]]
            indx+=1

            r = self.amp.getdata()
            if r[0]:
                d = r[1]
                sample = np.linspace(0,indx-1,self.amp.param.point+1).astype(np.int32)
                stt = temsts[:,sample[1:]]
                dd = np.vstack((d,stt))
                if self.expset.save_data:   self.store.data = np.hstack((self.store.data,dd))

                self.sig.eeg = d
                for i in range(stsnum): self.sig.state[stskeys[i]]=stt[i,]
                self.sig.event.set()
                indx = 0

            if clk-self.__clk>self.PHASES[self.currentphase]['duration']:
                self.currentphase=self.PHASES[self.currentphase]['next']
                self.__clk = clk
                self.phase_ev.set()

            if self.inphase('stop'):break

        if self.expset.save_data: self.store.savedata()
        self.stp.set()
        print '\ncore thread ended!'

