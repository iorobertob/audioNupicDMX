#-----------------------------------------------------------------------
# Name:        nupicAudioDMX
# Purpose:
#
# Author:      IO - Code
#
# Created:     10/11/2015
# Copyright:   (c) IO - Code 2015
# License:     see License.txt
#-----------------------------------------------------------------------

#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
#
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
"""
See README.md for details.
"""

"""
numpy - the language of pyaudio (& everything else)
pyaudio - access to the mic via the soundcard
os - to increment niceness
time - supports delays
sys - serial usb hardware
serial - to use usb interface
threading - 3 threads: main, audio and serial.
pyplot - to plot the sound frequencies
bitmaparray - encodes an array of indices into an SDR
TP10X2 - the C++ optimized temporal pooler (TP)
"""
import numpy #version
import random
import pyaudio
import os
import time
import sys
import serial
import threading
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.pyplot      import *

from nupic.encoders.sparse_pass_through_encoder    import SparsePassThroughEncoder
from nupic.research.TP10X2                         import TP10X2 as TP
from nupic.frameworks.opf.modelfactory             import ModelFactory # to create the nupic model
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager
from nupic.algorithms.anomaly_likelihood           import AnomalyLikelihood

import model_params     #this has to by a python file in the same folder

def destroy(e): sys.exit() # exit from the GUI

########################################################################################################
########################################################################################################
"""
C O N T R O L S
"""
SR          = 48000
bitRes      = 16
sizeBuffer  = 2**12     #4096
freqPerBin  =  int(SR/sizeBuffer)
numberOfBins= 1
indexes     = [
int(100/freqPerBin),
int(200/freqPerBin),
int(500/freqPerBin),
int(1000/freqPerBin),
]
ANOMALY_THRESHOLD   = 0.9   # To report when an anomaly exceeds a value. Not implemented yet. 
DMX_FLAG            = 1     # Used to stop the DMX thread only. 
plotAll             = 0     # Plot or not.
sendDMX             = 1     # Send DMX messages or not
HTM                 = 1     # Compute HTM or not
#######################################################################################################
########################################################################################################

pool=threading.BoundedSemaphore(1)

class nupicModel:
    
    def createModel(self):
        return ModelFactory.create(model_params.MODEL_PARAMS)

    
    def runModelAnomaly(self, model, amplitude, likelihoods):
      
        model.enableInference({'predictedField': 'binAmplitude'})
          
        self.result       = model.run       ({"binAmplitude" : amplitude})
        self.anomalyScore = self.result.inferences['anomalyScore']

        self.likelihood = likelihoods.anomalyProbability(amplitude, self.anomalyScore)

        # if anomalyScore > ANOMALY_THRESHOLD:
        #     print "Anomaly detected at [%s]. Anomaly score: %f."

        return (self.anomalyScore, self.likelihood)      


class Visualizations(threading.Thread):
    
    def __init__(self, semaphore, xAxis, noBins, indexes):

        threading.Thread.__init__(self)

        """
        Initialise constants, variables and buffers
        """
        self.noBins             = noBins    # Number of bins Windos is split into
        self.indexes            = indexes   # List of indexes of bins of interest, see bottom        
        self.xAxis              = xAxis     # Width of plot

        self.binValues          = []        # 2D: xAxis samples by noBins bins to plot (i.e. 200x4) - 4 lines in a plot 
        self.anomalyValues      = []        # 2D: xAxis anomaly samples by noBins bins' anomalies to plot (i.e. 200x4) - 4 lines in a plot 
        self.likelihoodValues   = []        # 2D: xAxis likelihood samples by noBins bins to plot (i.e. 200x4) - 4 lines in a plot 

        self.anomalyAv          = 0         # Averate of Normalised Anomalies Average. Still a float value
        self.likelihoodAv       = 0         # Average of Normalised Likelihoods Average. Still a float value.
        self.counterTime        = 0         # Counter to delay by some loops


        """
        Initialise deque arrays to append anomaly and audio values to. Use deque high performance holders
        """
        for i in range(self.noBins):
            self.binValues.append       ( deque([0.0]*self.xAxis,maxlen=self.xAxis))#To hold a frequency bin values over time.
            self.anomalyValues.append   ( deque([0.0]*self.xAxis,maxlen=self.xAxis))#Buffer to hold anomaly values
            self.likelihoodValues.append( deque([0.0]*self.xAxis,maxlen=self.xAxis))#Buffer to hold likelihood values

        self.timeAudioValues            = deque([0.0]*self.xAxis,maxlen=self.xAxis) # To hold time audio values and display them.
        self.anomalyAverage             = deque([0.0]*self.xAxis,maxlen=self.xAxis) # To hold anomalies averages and plot
        self.likelihoodAverage          = deque([0.0]*self.xAxis,maxlen=self.xAxis) # To hold likelihoods averages and plot



        """
        Interactive mode on
        """
        plt.ion()

    
        """
        Creating 3 subplots with xAxis width
        """
        plt.figure(num='NuPIC - Audio - DMX', figsize = (15,8))

        plt.subplot(411)  #firs location of a 2 x 1 plots grid - Frequency Spectrum
        self.freqPlot = plt.plot(range(0,self.xAxis),range(0,self.xAxis),'r',label="Frequency Spectrum")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        
        plt.subplot(412)  #second plot - Time Signal Scroll.
        self.timePlot = plt.plot(range(0,self.xAxis),range(0,self.xAxis),'g', label="Time Audio")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(-10000,10000)

        plt.subplot(413)  #location of next plot - Anomaly Scroll.
        self.anomalyPlot = plt.plot(range(0,self.xAxis),range(0,self.xAxis),'b', label="Anomaly in Time")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(-10,300.0)

        plt.subplot(414)  #location of next plot - Anomaly Scroll.
        self.anomalyPlot = plt.plot(range(0,self.xAxis),range(0,self.xAxis),'b', label="Anomaly Likelihood in Time")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(-10,300.0)

        # Ready to plot
        self.plottingFlag = 0


    def transferVars(self, audio, anomaly, likelihood):
            
            if (self.plottingFlag == 0):
                self.audio          = audio     #Dynamic
                self.anomalyVis     = anomaly   #Dynamic
                self.likelihood     = likelihood#Dynamic
                self.plottingFlag   = 0


    def run(self):

        while(self.onOff == 1):
            
            if (self.plottingFlag == 1):               
                    

                """
                Plot - Amplitude of the Frequency Bin, or Bins as scroll, shift vector and insert value at end, then plot.
                """
                plt.subplot(411)  #Four plots, 1 column first item 
                plt.cla()

                for i in range(0,self.noBins):
                    self.binValues[i].rotate(-1)
                    self.binValues[i][self.xAxis-1] = self.audio.ys[self.indexes[i]] 
                    plt.plot(self.binValues[i], label = "" + str((self.indexes[i]+1) * self.audio.binSize) + "Hz")

                plt.ylim(50,150)
                plt.legend(bbox_to_anchor=(0.15, 0.05, 0.5, .1), loc=3, ncol=self.noBins,mode="expand", borderaxespad=0.0)
                
                
                """
                Plot - Amplitude of the Audio Signal as scroll, shift vector and insert value at end, then plot.
                """
                self.timeAudioValues.rotate(-1)
                self.timeAudioValues[self.xAxis -1] = self.audio.audio[1]
                self.timePlot.set_ydata(self.timeAudioValues)                                                       
                  
                """
                Plot - Anomaly Value as scroll, shift vector and insert value at end, then plot. Comb filter could go out of this thread
                """ 
                plt.subplot(413)  #Four plots, 1 column, third item 
                plt.cla()
                self.anomalyAverage.rotate(-1)
                self.anomalyAverage[self.xAxis-1] = self.anomalyAv

                for i in range(self.noBins):

                    self.anomalyValues[i].rotate(-1)
                    self.anomalyValues[i][self.xAxis-1] = self.anomalyVis[i]
                    #### Comb Filter ###############################################################################################
                    # self.anomalyValues[i][self.xAxis-1] = (self.anomalyValues[i][self.xAxis-1] + self.anomalyValues[i][self.xAxis-2] 
                    #     + self.anomalyValues[i][self.xAxis-3] + self.anomalyValues[i][self.xAxis-4])/4
                    ################################################################################################################
                    plt.plot(self.anomalyValues[i], label = "Anly. " + str(i)) 
                                
                plt.plot(self.anomalyAverage, label = 'Avrg')
                plt.ylim(0,1.0)
                plt.legend(bbox_to_anchor=(0.4, 0.75, 0.6, .1), loc=3, ncol=self.noBins+1,mode="expand", borderaxespad=0.)  

                                                                   
                """
                Plot the Anomaly Likelihood Value as scroll, shift vector and insert value at end, then plot. TODO. Take Comb filter out of thread
                """ 
                plt.subplot(414)  #firs location of a 2 x 1 plots grid - Frequency Spectrum
                plt.cla()
                self.likelihoodAverage.rotate(-1)
                self.likelihoodAverage[self.xAxis-1] = self.likelihoodAv

                for i in range(self.noBins):

                    self.likelihoodValues[i].rotate(-1)
                    self.likelihoodValues[i][self.xAxis-1] = self.likelihood[i]##numpy.random_sample()*255
                    #### Comb Filter ###############################################################################################
                    # self.likelihoodValues[i][self.xAxis-1] = (self.likelihoodValues[i][self.xAxis-1] + self.likelihoodValues[i][self.xAxis-2] 
                    #     + self.likelihoodValues[i][self.xAxis-3] + self.likelihoodValues[i][self.xAxis-4])/4
                    ################################################################################################################
                    plt.plot(self.likelihoodValues[i], label = "Lklhd. " + str(i)) 
                
                plt.plot(self.likelihoodAverage, label = 'Avrg')
                plt.ylim(0,1.0)
                plt.legend(bbox_to_anchor=(0.4, 0.75, 0.6, .1), loc=3, ncol=self.noBins+1,mode="expand", borderaxespad=0.) 
                                           
                plt.show(block = False)
                plt.draw()                

                self.plottingFlag = 0


class AudioStream:

    def __init__(self):

        """
        Sampling details
        rate: The sampling rate in Hz of my soundcard
        sizeBuffer: The size of the array to which we will save audio segments (2^12 = 4096 is very good)
        """
        self.audioStarted = 0
        self.rate=SR
        self.binSize=int(SR/sizeBuffer)
        if (bitRes == 16):
            width = 2
        if (bitRes == 8):
            width = 1
        if (bitRes == 32):
            width = 4       


   
        """
        Creting the audio stream from our mic, Callback Mode.
        """
        p = pyaudio.PyAudio()
        

        """
        Setting up the array that will handle the timeseries of audio data from our input
        """
        if (bitRes == 16):
            self.audio = numpy.empty((sizeBuffer),dtype="int16")
            print "Using 16 bits"
        if (bitRes == 8):
            self.audio = numpy.empty((sizeBuffer),dtype="int8")
            print "Using 8 bits"
        if (bitRes == 32):
            self.audio = numpy.empty((sizeBuffer),dtype="int32")
            print "Using 32 bits"


    
        def callback(in_data,frame_count, time_info, status):
            self.audio = numpy.fromstring(in_data,dtype=numpy.int16)
            self.ys = self.fft(self.audio)
            self.ys = 20*numpy.log10(self.ys)
            print('Bin 10 = ' + str(self.ys[10]))
            self.audioStarted = 1
            return (self.ys, pyaudio.paContinue)

        """
        Open the Audio Stream.
        Start separate thread
        """    
        self.inStream = p.open(format   = p.get_format_from_width(width, unsigned=False),
                               channels =1,
                               rate     =self.rate,
                               input    =True,
                               frames_per_buffer=sizeBuffer,
                               stream_callback  = callback)
                                                                                                                                   
                                                                                                                                           
    def fft(self, audio):
            """
            Fast fourier transform conditioning
            Output:     'output' contains the strength of each frequency in the audio signal
            frequencies are marked by its position in 'output'
            Method:      Use numpy's FFT (numpy.fft.fft)
            Great info here: http://stackoverflow.com/questions/4364823/how-to-get-frequency-from-fft-result
            """
            left = numpy.abs(numpy.fft.fft(audio))
            output = left
            return output
        


class Main:
    
    def __init__(self, noBins, indexes, sizeBuffer):

        """
        Create & RunAudioStream object, SampleRate=48kHz, Buffersize=2*12, lowpass=10kHz, highpass=50Hz, 16 bits.
        """     
        audioObject = AudioStream()               
        audioObject.inStream.start_stream()
        print 'Start Audio Stream'
        while (audioObject.audioStarted == 0):1#loop to wait the audio to start

        

        """
        Create DMX object, start thread. Outputs a default DMX value until changed in other threads
        """  
        if sendDMX == 1:      
            dmx = pydmx(pool, 21)
            dmx.start()
            print 'Start DMX Stream'

        """
        Start the NuPIC model 
        """
        if HTM == 1:
            self.nupic          = nupicModel()
            self.models         = [self.nupic.createModel() for i in range(noBins)]
            self.anomaly        = [i for i in range(noBins)]
            self.likelihood     = [i for i in range(noBins)]
            self.likelihoods    = [AnomalyLikelihood() for i in range(noBins)]
            print 'Start NuPIC models'


        """
        Initialise the plots, 100 is the width of the plot.
        """
        if plotAll == 1:
            vis = Visualizations(pool, 100,noBins, indexes)
            vis.transferVars(audioObject, self.anomaly, self.likelihood)
            vis.onOff = 1
            vis.start()
            print 'Start MatPlotLib'

            
        """
        Print out the inputs
        """
        print "Sampling rate (Hz):\t"    + str(audioObject.rate)
        print "Hz per Bin:\t\t"          + str(audioObject.rate/sizeBuffer)
        print "Buffersize:\t\t"          + str(sizeBuffer)        


        """
        Start the Main Thread Loop.
        """
        self.counterTime = 0
        self.modelRunning = 1
        
        while self.modelRunning == 1:
            
            try:

                """
                NUPIC MODEL - Run the NuPIC model and get the anomaly score back. Feed on bin only.
                """
                if HTM == 1:
                    for i in range(noBins):
                        self.anomaly[i], self.likelihood[i] = self.nupic.runModelAnomaly( 
                            self.models[i] , 
                            audioObject.ys[indexes[i]],
                            self.likelihoods[i])

                    self.anomalyAv    = numpy.sum(self.anomaly)   /noBins
                    self.likelihoodAv = numpy.sum(self.likelihood)/noBins #Range expanded and clipped for DMX Lighting reasons!
                    print ("Anomaly " + str(self.anomalyAv))

                """             
                DMX - Pass Likelihood value to the DMX Thread. Clip values below 0.
                """
                if sendDMX == 1 and HTM ==1:
                    if self.likelihoodAv < 0:
                        dmx.anomalyDMX = 0                    
                    if self.likelihoodAv > 0.17:
                        #dmx.anomalyDMX = int(self.anomalyAv*255)#CHANGE OR ADD self.anomalyLikelihood
                        dmx.anomalyDMX = int(self.likelihoodAv*300 -50)#CHANGE OR ADD self.anomalyLikelihood
                if sendDMX ==1 and HTM == 0:
                    if 1 < audioObject.ys[10] and  audioObject.ys[10] < 255:
                        #print ('simon' + str(int(audioObject.ys[10])) )
                        #dmx.anomalyDMX = int(audioObject.ys[10])# Send the audio value as DMX
                        dmx.anomalyDMX = random.randint(5,50)
                    else:
                        dmx.anomalyDMX = 0


                """
                PLOT - Pass values to Plot Thread
                """
                if plotAll == 1:
                    if vis.plottingFlag == 0:
                        vis.anomalyVis      = self.anomaly
                        vis.likelihood      = self.likelihood
                        vis.audio           = audioObject                    
                        vis.likelihoodAv    = self.likelihoodAv  
                        vis.anomalyAV       = self.anomalyAv            
                        vis.plottingFlag    = 1                      

                                       
            except KeyboardInterrupt:
                self.modelRunning  = 0
                print 'Trying to stop - Keyboard Interrupt'
                pass

            except Exception, err:
                self.modelRunning  = 0
                print 'Trying to stop - Exception, Error'
                print err
                pass
                
        
        if plotAll == 1:
            self.vis.onOff          = 0     #Visualisations 
            self.vis.join()
            plt.close()                     #Matplotlib 

        audioObject.inStream.stop_stream()  #PyAudio
        audioObject.inStream.close()        #PyAudio 

        if sendDMX == 1:
            global DMX_FLAG
            DMX_FLAG                = 0     #Serial
            dmx.blackout()                  #Serial
            dmx.close_serial()              #Serial
            dmx.join()                      #Serial
                                                                      
        print("Exit PyAudio, Matplotlib & Serial")
        sys.exit()                                                                                  
    


class pydmx(threading.Thread):
    """
    D M X  Class for Enttec USB Pro serial porotocol.
    Select the name of the usb port, use baud rate of 57600
    fills an array with the Enteec protocol, 512 channels,
    taking the anomaly value from the Main Thread and using it 
    as chanell value.
    """
    def __init__(self, semaphore, port_number = "/dev/tty.usbserial-EN169205"):
        
        global DMX_FLAG
        DMX_FLAG = 1
        self.anomalyDMX = 20
        threading.Thread.__init__(self)
        
        self.channels       = [0 for i in range(512)]
        self.port_number    = port_number
        self.semaphore      = semaphore
        
        # DMX_USB Interface variables
        self.SOM_VALUE = 0x7E # SOM = Start of Message
        self.EOM_VALUE = 0xE7 # EOM = End of Message
        
        # Lables:
        self.REPROGRAM_FIRMWARE_LABEL           = 1
        self.PROGRAM_FLASH_PAGE_LABEL           = 2
        self.GET_WIDGET_PARAMETERS_LABEL        = 3
        self.SET_WIDGET_PARAMETERS_LABEL        = 4
        self.RECEIVED_DMX_LABEL                 = 5
        self.OUTPUT_ONLY_SEND_DMX_LABEL         = 6
        self.RDM_SEND_DMX_LABEL                 = 7
        self.RECIEVE_DMX_ON_CHANGE_LABEL        = 8
        self.RECIEVED_DMX_CHANGE_OF_STATE_LABEL = 9
        self.GET_WIDGET_SERIAL_NUMBER_LABEL     = 10
        self.SEND_RDM_DISCOVERY_LABEL           = 11
        self.INVALID_LABEL                      = 0xFF
        
        # Initialize serial port
        try:
            # Open serial port with receive timeout
            self.ser = serial.Serial(port="/dev/tty.usbserial-EN169205", baudrate=57600, timeout=1)
        
        except:
            print "dmx_usb.__init__: ERROR: Could not open %u" % (port_number+1)
        #sys.exit(0)
        else:
            print "dmx_usb.__init__: Using %s" % (self.ser.portstr)
    
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()
    
    def stopped(self):
        return self._stop.isSet()
    
    # Low level functions (for inside use only)
    def transmit(self, label, data, data_size):
        self.tem_data = [chr(self.SOM_VALUE)] + \
            [chr(label)] + \
            [chr(data_size & 0xFF)] + \
            [chr((data_size >> 8) & 0xFF)] +\
            data + \
            [chr(self.EOM_VALUE)]
            #Send data to serial port
        self.ser.write(self.tem_data)
        print self.ser.outWaiting()

    # Higher level functions:
    def set_channel(self, channel, value=0):
        # Channel = DMX Channel (1-512)
        # Value = Strength (0-100%)
        self.channels[channel] = value

    
    def update_channels(self):
        '''Send all 512 DMX Channels from channels[] to the hardware:
        update_channels()'''
        # This is where the magic happens
        #print "dmx_usb.update_channels: Updating Anomaly:" + str(self.anomalyDMX)
        self.int_data = [0] + self.channels
        self.msg_data = [chr(self.int_data[j]) for j in range(len(self.int_data))]
        self.transmit(self.OUTPUT_ONLY_SEND_DMX_LABEL, self.msg_data, len(self.msg_data))

    
    def close_serial(self):
        self.ser.close()
        print("Serial closed")    
 
    def blackout(self):
        print "DMX Blackout"
        self.channels = [0 for i in range(512)]
        self.update_channels()
    
    def run(self):
        print "Run DMX Task"

        global DMX_FLAG

        self.blackout() 

        
        while (DMX_FLAG == 1):
            
            ##Set all channels with desired values
            ##this function will only update the buffer
            ##will not update the output in the Enttec device
            #dmx.set_channel(0,self.anomaly)#STROBE
            self.set_channel(1,self.anomalyDMX)#RED YELLOW
            self.set_channel(2,self.anomalyDMX)#GREEN PURPLE
            self.set_channel(3,self.anomalyDMX)#BLUE WHITE
            #dmx.set_channel(4,self.anomaly)#MOTOR
            #print 'sending dmx'
            #Send data to Enttec Device
            self.update_channels()
        
        #Clear Output, set all channels to 0's
        print 'Out of dmx'

        DMX_FLAG = 0
        self.blackout()
        self.close_serial()
        self.stop()


"""
Entrance to program
"""



nupicAudioDMX = Main(numberOfBins,indexes, sizeBuffer) #4 bins 
