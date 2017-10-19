#!user/bin/python
# -*-coding:utf-8-*-

#FileName: bcitypes.py
#Version: 1.0
#Author: Jingsheng Tang
#Date: 2017/8/11
#Email: mrtang@nudt.edu.cn
#Github: trzp

import os
from threading import Event

class Expset:
    experiment_name = '312 bci experiment'
    subject_name = 'shuaiguo'
    session = 1
    run = 1
    path = os.path.split(os.sys.argv[0])[0]
    Amp = 'actichamp' #or 'signal_generator'
    save_data = False
    amp_channels = 4
    amp_samplingrate = 200
    signal_generator_waveform = 'sin'
    signal_generator_frequency = 20
    signal_generator_gain = 50


class EEG:
    event = Event()
    eeg = None
    state = {}
    samplingrate = 200
    eegchs = 0

class EEGparam:
    samplingrate = 200
    eegchannels = 0
    point = 10

class States:
    state = {}
