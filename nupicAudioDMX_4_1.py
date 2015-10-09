#-------------------------------------------------------------------------------
# Name:        nupicAudioDMX_2_0
# Purpose:
#
# Author:      IO - Code
#
# Created:     05/10/2015
# Copyright:   (c) IO - Code 2015
# License:     see License.txt
#-------------------------------------------------------------------------------

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
import pyaudio
import os
import time
import sys
import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.pyplot import *
from nupic.encoders.sparse_pass_through_encoder import SparsePassThroughEncoder
from nupic.research.TP10X2 import TP10X2 as TP
from collections import deque



from pkg_resources import resource_filename

from nupic.frameworks.opf.modelfactory import ModelFactory # to create the nupic model
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager

from nupic.algorithms.anomaly_likelihood import AnomalyLikelihood

#this has to by a python file in the same folder
import model_params



def destroy(e): sys.exit() # exit from the GUI

pool=threading.BoundedSemaphore(1)
anomaly = 10
flag = 1


_INPUT_DATA_FILE = resource_filename(
  "nupic.datafiles", "extra/hotgym/rec-center-hourly.csv"
)
_OUTPUT_PATH = "anomaly_scores.csv"

_ANOMALY_THRESHOLD = 0.9




class nupicModel:
    
    def createModel(self):
            return ModelFactory.create(model_params.MODEL_PARAMS)

    
    def runModelAnomaly(self, model, amplitude):
      
        model.enableInference({'predictedField': 'binAmplitude'})
          
        result = model.run({"binAmplitude" : amplitude})
        anomalyScore = result.inferences['anomalyScore']

        #likelihood = AnomalyLikelihood.anomalyProbability(amplitude, anomalyScore)

        if anomalyScore > _ANOMALY_THRESHOLD:
            print "Anomaly detected at [%s]. Anomaly score: %f."

        return (anomalyScore, 1)      


class Visualizations:
    
    def __init__(self, xs, xAxis):

        plt.ion()         #interactive mode on

        plt.subplot(311)  #firs location of a 2 x 1 plots gri - Frequency Spectrum
        self.freqPlot = plt.plot(range(0,xAxis),range(0,xAxis),'r',label="Frequency Spectrum")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(0,100000)

        plt.subplot(312)  #second plot - Time Signal Scroll.
        self.timePlot = plt.plot(range(0,xAxis),range(0,xAxis),'g', label="Time Audio")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(-5000,5000)

        plt.subplot(313)  #location of next plot - Anomaly Scroll.
        self.anomalyPlot = plt.plot(range(0,xAxis),range(0,xAxis),'b', label="Anomaly in Time")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(-10,300.0)


    def updatePlot(self, ys, binAmplitude, binValues1, timeAudioValues, anomalyValues, anomaly, audio1, xAxis ):

        binValues1.rotate(-1)
        binValues1[xAxis -1] = binAmplitude
        self.freqPlot.set_ydata(binValues1)# Plot the Frequency Spectrum
                                           
        # Plot the TimeScale of the Audio in a scroll, by shifting to the right and filling last element.
        timeAudioValues.rotate(-1)
        timeAudioValues[xAxis -1] = audio1
        self.timePlot.set_ydata(timeAudioValues)
                                                   
        # Normalize anomaly from 0 to 255, integers only.
        anomaly = int(anomaly * 255)
                                                   
         #Shift anomalyValues array (for scrolling) to the right, and fill the last element with new Anomaly value.
        anomalyValues.rotate(-1)
        anomalyValues[xAxis-1] =  anomaly
        # 4 pole moving average, so smooth changes in Anomaly values
        anomalyValues[xAxis-1] =  (anomalyValues[xAxis-1] + anomalyValues[xAxis-2] + anomalyValues[xAxis-3] + anomalyValues[xAxis-4])/4
        self.anomalyPlot.set_ydata(anomalyValues)
                                                           
        #print "Value of Anomaly: " + str(self.anomalyValues[xAxis-1])
                                                           
        #self.counterTime += 1
        #Update only every 200 times
        #if (self.counterTime > 10):
        #   plt.show(block = False)
        #   plt.draw()
        #   self.counterTime = 0
        plt.show(block = False)
        plt.draw()



class AudioStream:
    
    def __init__(self):

        
        """
        Sampling details
        rate: The sampling rate in Hz of my soundcard
        buffersize: The size of the array to which we will save audio segments (2^12 = 4096 is very good)
        """
        rate=48000
        self.buffersize=2**12
        
        
        """
        Filters in Hertz
        highHertz: lower limit of the bandpass filter, in Hertz
        lowHertz: upper limit of the bandpass filter, in Hertz
        max lowHertz = (buffersize / 2 - 1) * rate / buffersize
        """
        highHertz = 500
        lowHertz = 10000
        
    
        """
        Convert filters from Hertz to bins
        highpass: convert the highHertz into a bin for the FFT
        lowpass: convert the lowHertz into a bin for the FFt
        NOTES:
        highpass is at least the 1st bin since most mics only pick up >=20Hz
        lowpass is no higher than buffersize/2 - 1 (highest array index)
        passband needs to be wider than size of numInput - not checking for that
        """
        self.highpass = max(int(highHertz * self.buffersize / rate),1)
        self.lowpass = min(int(lowHertz * self.buffersize / rate), self.buffersize/2 - 1)
        
    
        """
        Creting the audio stream from our mic, Callback Mode.
        """
        p = pyaudio.PyAudio()
        width = 2#8 BIT
    
        def callback(in_data,frame_count, time_info, status):
            self.audio = numpy.fromstring(in_data,dtype=numpy.int16)
            return (self.audio, pyaudio.paContinue)

        """
        Open the Audio Stream.
        """    
        self.inStream = p.open(format = p.get_format_from_width(width, unsigned=False),
                               channels=1,
                               rate=rate,
                               input=True,
                               frames_per_buffer=self.buffersize,
                               stream_callback = callback)
        
        """
        Setting up the array that will handle the timeseries of audio data from our input
        """
        self.audio = numpy.empty((self.buffersize),dtype="int16")

        #initialise anomaly
        self.anomaly = 0
        self.anomalyGrad = 127;


        """
        Setup the X axis array.
        """
        bin = range(self.highpass,self.lowpass)
        xs = numpy.arange(len(bin))*rate/self.buffersize + highHertz

        # Length of the plog window.
        self.xAxis = 500  #Width of plt.

        
        """
        Initialise the plots
        """
        self.vis = Visualizations(xs, self.xAxis)


        """
        Initialise deque arrays to append anomaly and audio values to
        """
        self.binValues1 = deque([0.0]*self.xAxis,maxlen=self.xAxis)   #To hold a frequency bin values over time.
        
        self.anomalyValues = deque([0.0]*self.xAxis,maxlen=self.xAxis)# Buffer to hold anomaly values - Use collections.deque high performance holders.

        self.timeAudioValues = deque([0.0]*self.xAxis,maxlen=self.xAxis)   #To hold time audio values and display them.


        """
        Start the Audio Thread.
        """
        self.inStream.start_stream()


        """
        Create DMX object
        """
        dmx = pydmx(pool, 21)


        """
        Start the DMX Thread
        """
        dmx.start()

        """
        Start the DMX Thread
        """
        self.nupic = nupicModel()
        self.model = self.nupic.createModel()

            
        """
        Print out the inputs
        """
        print "Sampling rate (Hz):\t" + str(rate)
        print "Passband filter (Hz):\t" + str(highHertz) + " - " + str(lowHertz)
        print "Passband filter (bin):\t" + str(self.highpass) + " - " + str(self.lowpass)
        print "Bin difference:\t\t" + str(self.lowpass - self.highpass)
        print "Hz per Bin:\t\t" + str(rate/self.buffersize)
        print "Buffersize:\t\t" + str(self.buffersize)        


        """
        Start the Main Thread Loop.
        """
        self.counterTime = 0
        
        while True:
            try:
                print("Start of Audio Process")                  
                self.processAudio()
                                       
            except KeyboardInterrupt:
                                           
                self.inStream.stop_stream() #PyAudio
                self.inStream.close()       #PyAudio
                                                       
                plt.close()                 #Matplotlib
                                                           
                flag = 0                   #Serial
                dmx.blackout()              #Serial
                dmx.close_serial()          #Serial
                dmx.join()                  #Serial
                                                                           
                print("sys.exit() Exit PyAudio, Matplotlib & Serial")
                sys.exit()
                                                                                   
    def processAudio(self):
                                                                                       
            global anomaly
               
            """
            Get int array of strength for each bin of frequencies via fast fourier transform
            Get the indices of the strongest frequencies (the top 'numInput')
            Scale the indices so that the frequencies fit to within numCols
            Pick out the unique indices (we've reduced the mapping, so we likely have multiples)
            Encode those indices into an SDR via the SparsePassThroughEncoder
            Cast the SDR as a float for the TP
            """
            ys = self.fft(self.audio, self.highpass, self.lowpass)
            
                                               
            """
            NUPIC MODEL
            Run the NuPIC model and get the anomaly score back.
            Feed one bin value only. 
            """                                                                               
            self.anomaly, self.likelihood = self.nupic.runModelAnomaly(self.model, ys[20])

                
            """
            Call the update of the plots. 
            """
            self.vis.updatePlot(ys,ys[20], self.binValues1, self.timeAudioValues, self.anomalyValues, self.anomaly, self.audio[1], 500)
            
            
            """
            Pass anomaly value to the DMX Thread.
            """
            pool.acquire()
            anomaly = int(self.anomalyValues[self.xAxis-1])
            pool.release()
            
                                                                                                                                           
                                                                                                                                           
    def fft(self, audio, highpass, lowpass):
            """
            Fast fourier transform conditioning
            Output:
            'output' contains the strength of each frequency in the audio signal
            frequencies are marked by its position in 'output':
            frequency = index * rate / buffesize
            output.size = buffersize/2
            Method:
            Use numpy's FFT (numpy.fft.fft)
            Find the magnitude of the complex numbers returned (abs value)
            Split the FFT array in half, because we have mirror frequencies
            (they're the complex conjugates)
            Use just the first half to apply the bandpass filter
            Great info here: http://stackoverflow.com/questions/4364823/how-to-get-frequency-from-fft-result
            """
            left = numpy.abs(numpy.fft.fft(audio))
            output = left[highpass:lowpass]
            return output



class pydmx(threading.Thread):
    """
    D M X  Class for Enttec USB Pro serial porotocol.
    Select the name of the usb port, use baud rate of 57600
    fills an array with the Enteec protocol, 512 channels,
    taking the anomaly value from the Main Thread and using it 
    as chanell value.
    """
    def __init__(self, semaphore, port_number = "/dev/tty.usbserial-EN169205"):
        
        self.flag = 1
        
        threading.Thread.__init__(self)
        
        self.channels = [0 for i in range(512)]
        self.port_number = port_number
        self.semaphore = semaphore
        self.counter = 6000
        self.anomaly = 127
        
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
            self.ser = serial.Serial(port=port_number, baudrate=57600, timeout=1)
        
        except:
            print "dmx_usb.__init__: ERROR: Could not open %u" % (port_number+1)
        #sys.exit(0)
        else:
            print "dmx_usb.__init__: Using %s" % (self.ser.portstr)
    
    #self._stop = threading.Event()

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

    # Higher level functions:
    def set_channel(self, channel, value=0):
        # Channel = DMX Channel (1-512)
        # Value = Strength (0-100%)
        self.channels[channel] = value
    
    def update_channels(self):
        '''Send all 512 DMX Channels from channels[] to the hardware:
        update_channels()'''
        # This is where the magic happens
        print "dmx_usb.update_channels: Updating Anomaly:" + str(self.anomaly)
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
        print "  self.blackout()"
        self.blackout()
        
        while (flag == 1):
            
            self.semaphore.acquire()
            global anomaly
            self.anomaly = anomaly
            self.semaphore.release()
            
            ##Set all channels with desired values
            ##this function will only update the buffer
            ##will not update the output in the Enttec device
            
            #dmx.set_channel(0,self.anomaly)#STROBE
            self.set_channel(1,self.anomaly)#RED YELLOW
            self.set_channel(2,self.anomaly)#GREEN PURPLE
            self.set_channel(3,self.anomaly)#BLUE WHITE
            #dmx.set_channel(4,self.anomaly)#MOTOR
            
            #Send data to Enttec Device
            self.update_channels()
        
        #Clear Output, set all channels to 0's
        
        print "Flag:\t\t" + str(self.flag)
        
        self.blackout()
        self.close_serial()


"""
Entrance to program
"""
audiostream = AudioStream() 
