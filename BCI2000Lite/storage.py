#!user/bin/python
# -*-coding:utf-8-*-

#FileName: storage.py
#Version: 1.0
#Author: Jingsheng Tang
#Date: 2017/8/9
#Email: mrtang@nudt.edu.cn
#Github: trzp

import os, time
import numpy as np
from bcitypes import *
import scipy.io


class Storage(object):
    def __init__(self,expset,param,statekeys):
        self.expset = expset
        head = self.expset.subject_name +'-S%iR'%(self.expset.session)
        extension = '.mat'
        filenum = self.expset.run
        filename = head+str(filenum)+extension
        newfilename = self.expset.path+'//'+filename
        if not os.path.exists(self.expset.path):
            os.makedirs(self.expset.path)
        else:
            files = os.listdir(self.expset.path)
            nums = [self.getnum(f,head,extension) for f in files if self.getnum(f,head,extension)>-1]
            if nums!=[]:    newfilename = self.expset.path+'//'+head+str(max(nums)+1)+extension
        self.data_file = newfilename

        self.param = param
        self.statekeys = statekeys
        self.eegrows = expset.amp_channels
        self.staterows = len(statekeys)
        rows = self.staterows+self.eegrows
        self.cols = int(expset.amp_samplingrate/20)
        self.data = np.zeros((rows,self.cols),dtype=np.float64)

        self.buf = {}
        self.buf['ExperimentName']=self.expset.experiment_name
        self.buf['SubjectName']=self.expset.subject_name
        self.buf['Time']=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        self.buf['SamplingRate']=int(self.param.samplingrate)
        self.buf['EEGChannels']=int(self.param.eegchannels)

    def getnum(self,file,head,extension):
        hi = file.find(head)
        ei = file.find(extension)
        if hi==-1 or ei==-1:
            return -1
        else:
            try:
                num = int(file[hi+len(head):ei])
                return num
            except:
                return -1

    def savedata(self):#channels x points
        self.data = self.data[:,self.cols:]
        self.buf['EEG']=self.data[:self.eegrows,:]
        for i in range(self.staterows):
            self.buf[self.statekeys[i]]=self.data[self.eegrows+i,:]
        scipy.io.savemat(self.data_file,self.buf)

if __name__ == '__main__':
    import time
    import numpy as np
    store = Storage()
    exp = Expset()
    parm = EEGparam()
    store.create_file(exp)
    store.write_info(parm,'tang')
    i = 0
    while True:
        i += 1
        store.write_data(np.array([[1,2,3,4,5],[11,22,33,44,55]],dtype=np.float64))
        time.sleep(0.05)
        if i>1800:break
    store.close_file()





