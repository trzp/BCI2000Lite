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

        
class FastP3Classification(P3Classification):
    def __init__(self,path,expset,numofseq,cubedim):
        super(FastP3Classification,self).__init__(path,expset)
        self.windownum = math.ceil(self.parm['window'][1]*self.parm['samplingrate']/1000.)

        self.signal = np.zeros((expset.amp_channels,50))
        self.code = -1*np.ones(50)
        self.cubedim = cubedim
        if 1 not in self.cubedim:   self.flashnum = numofseq*sum(self.cubedim)
        else:   self.flashnum = self.numofseq*np.prod(self.cubedim)
        self.res = (0,0)

    def update(self,sig):
        self.signal = np.hstack((self.signal,sig.eeg))
        self.code = np.hstack((self.code,sig.state['code']))
        temcode = copy(self.code)
        temcode[-self.windownum:] = -1  #去掉尾部信号,保留足够时间确保最后一个能切片完成
        ind = np.where((temcode[:-1]==-1) & (temcode[1:]>=0))[0]+1
        if ind.size >= self.flashnum:   #已经有足够多的信号
            firstind = ind[-self.flashnum]
            temcode[:firstind] = -1    #去掉前部多余信号
            self.signal = self.signal[:,firstind-40:] #只保留一段有用信号，节约内存
            self.code[:firstind] = -1
            self.code = self.code[firstind-40:]
            temcode = temcode[firstind-40:]
            self.res = self.rc_estimate(self.signal,temcode,self.cubedim)
        return self.res

class FastP3andTon:
    def __init__(self,path,expset,numofseq,cubedim,ev):
        self.FastP3 = FastP3Classification(path,expset,numofseq,cubedim)
        self.threshold = 100
        self.ev = ev
        self.lastres = self.currentres = 0


    def update(self,sig):
        res = self.FastP3.update(sig)
        tonsig = self.FastP3.signal[-1,:]    #0号通道
        print sum(abs(tonsig[-80:]))
        if sum(abs(tonsig[-80:]))>self.threshold:   self.currentres = 1
        else:   self.currentres = 0
        if self.currentres-self.lastres>0:self.ev.set()
        self.lastres = self.currentres
        return res




