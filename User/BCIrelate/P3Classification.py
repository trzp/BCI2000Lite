#!user/bin/python
# -*-coding:utf-8-*-

#FileName: signalprocess.py
#Version: 1.0
#Author: Jingsheng Tang
#Date: 2017/8/29
#Email: mrtang@nudt.edu.cn
#Github: trzp

from __future__ import division
import scipy.signal
import scipy.io as sio
import numpy as np
import win32api
import math
from copy import copy

class P3Classification(object):
    def __init__(self,path,expset):
        self.parm = sio.loadmat(path)
        for key in self.parm.keys():
            try:self.parm[key]=self.parm[key][0].astype(np.float32)
            except:pass
        self.parm['p3_channels']=(self.parm['p3_channels']-1).astype(np.int32)
        if expset.amp_samplingrate != self.parm['samplingrate']:
            win32api.MessageBox(0,"amplifier samplingrate and trainning samplingrate is not match! we will using the system samplingrate!")
            self.parm['p3_channels'] = expset.amp_samplingrate

    def rc_estimate(self,sig,stimcode,cubedim):
        signal = sig[self.parm['p3_channels'],:]
        code = stimcode
        signal_p300_filtered = scipy.signal.lfilter(self.parm['p3filter'],1,signal)
        num_window = (self.parm['window'] * self.parm['samplingrate'][0].astype(np.int32)/1000.).astype(np.int32)
        winL = np.diff(num_window)[0]
        num_base_window = (self.parm['base_window'] * self.parm['samplingrate'][0]/1000).astype(np.int32)
        ind = np.where((code[:-1]==-1) & (code[1:]>=0))[0]+1
        xx = ind.size
        tscores = np.zeros(xx)
        for i in range(xx):
            slice = signal_p300_filtered[:,ind[i]+num_window[0]:ind[i]+num_window[1]].flatten()
            mean_bl = np.mean(signal_p300_filtered[:,ind[i]+num_base_window[0]:ind[i]+num_base_window[1]-1],axis=1)
            mean_bl = np.repeat(mean_bl,winL)
            tscores[i] = np.sum((slice - mean_bl)*self.parm['mud'])
            
        ocode = code[ind]
        ucode = np.unique(ocode)
        newscore = np.zeros((2,ucode.size))
        for i in range(ucode.size):
            newscore[0,i]=ucode[i]
            newscore[1,i]=np.mean(tscores[np.where(ocode==ucode[i])])

        rscore = newscore[:,:cubedim[0]]
        cscore = newscore[:,cubedim[0]:]
        rs = np.argsort(rscore)[1,:]
        cs = np.argsort(cscore)[1,:]
        r = rscore[0,rs[-1]]
        c = cscore[0,cs[-1]]
        return int(r),int(c-cubedim[0]),newscore
