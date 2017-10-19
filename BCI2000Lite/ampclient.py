#!user/bin/python
# -*-coding:utf-8-*-

#FileName: ampclient.py
#Version: 1.0
#Author: Jingsheng Tang
#Date: 2017/8/11
#Email: mrtang@nudt.edu.cn
#Github: trzp


import mmap
import struct
import numpy as np
from bcitypes import *
import time
import random


class AmpClient(object):
    '''
    the pycorder acquire data for every 50ms. this class is used to read these data
    from a piece of shared memory named '__eeg_from_pycorder__'.
    '''
    def __init__(self):
        self.param = EEGparam()
        self.shm = mmap.mmap(0,24,access=mmap.ACCESS_READ,tagname='__eeg_from_pycorder__')
        self.shm.seek(0)
        fs,chs,p = struct.unpack('3d',self.shm.read(24))
        self.size = int((4+chs*p)*8)
        self.shm = mmap.mmap(0,self.size,access=mmap.ACCESS_READ,tagname='__eeg_from_pycorder__')
        self.databytesize = int(chs*p*8)
        self.ind = 0

        self.param.samplingrate = int(fs)
        self.param.eegchannels = int(chs)
        self.param.point = int(p)

    def freshind(self):
        self.shm.seek(24)
        self.ind = struct.unpack('d',self.shm.read(8))[0]

    def getdata(self):
        self.shm.seek(24)
        ind = struct.unpack('d',self.shm.read(8))[0]
        d = ind - self.ind

        if d>1:
            print time.strftime('%H:%M:%S   ',time.localtime(time.time())) + 'lost %i data'%(d)

        if d>0:
            self.ind = ind
            self.shm.seek(32)
            data = np.fromstring(self.shm.read(self.databytesize),dtype=np.float64).reshape((self.param.eegchannels, self.param.point))
            return 1,data
        else:
            return 0,0


class SigGen(object):
    def __init__(self,expset):
        self.expset = expset
        self.param = EEGparam()
        self.param.samplingrate = expset.amp_samplingrate
        self.param.eegchannels = expset.amp_channels
        self.param.point = int(self.param.samplingrate/20)
        self.F = expset.signal_generator_frequency
        self.G = expset.signal_generator_gain
        self.clk = time.clock()
        self.__baset = np.linspace(0,0.05,self.param.point+1)[:-1]

    def freshind(self):
        pass

    def getdata(self):
        ct = time.clock()
        if ct-self.clk>0.05:
            ts = self.__baset + ct
            if self.expset.signal_generator_waveform == 'sin':  val = np.sin(2*np.pi*self.F*ts)*self.G
            else:   val = np.array([0.05*random.randint(-2000,2000) for i in range(self.param.point)])
            data = np.repeat(val,self.param.eegchannels).reshape(self.param.point,self.param.eegchannels).transpose()
            self.clk = ct
            return 1,data
        else:
            return 0,0


