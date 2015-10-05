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
from nupic.encoders.sparse_pass_through_encoder import SparsePassThroughEncoder
from nupic.research.TP10X2 import TP10X2 as TP
from collections import deque

def destroy(e): sys.exit() # exit from the GUI

pool=threading.BoundedSemaphore(1)
anomaly = 10

class Visualizations:

  def calcAnomaly(self, actual, predicted):
    """
    Calculates the anomaly of two SDRs

    Uses the equation presented on the wiki:
    https://github.com/numenta/nupic/wiki/Anomaly-Score-Memo

    To put this in terms of the temporal pooler:
      A is the actual input array at a given timestep
      P is the predicted array that was produced from the previous timestep(s)
      [A - (A && P)] / [A]
    Rephrasing as questions:
      What bits are on in A that are not on in P?
      How does that compare to total on bits in A?

    Outputs 0 is there's no difference between P and A.
    Outputs 1 if P and A are totally distinct.

    Not a perfect metric - it doesn't credit proximity
    Next step: combine with a metric for a spatial pooler
    """
    combined = numpy.logical_and(actual, predicted)
    delta = numpy.logical_xor(actual,combined)
    delta_score = sum(delta)
    actual_score = float(sum(actual))
    return delta_score / actual_score


  def compareArray(self, actual, predicted):
    """
    Produce an array that compares the actual & predicted

    'A' - actual
    'P' - predicted
    'E' - expected (both actual & predicted
    ' ' - neither an input nor predicted
    """
    compare = []
    for i in range(actual.size):
      if actual[i] and predicted[i]:
        compare.append('E')
      elif actual[i]:
        compare.append('A')
      elif predicted[i]:
        compare.append('P')
      else:
        compare.append(' ')
    return compare


  def hashtagAnomaly(self, anomaly):
    """
    Basic printout method to visualize the anomaly score (scale: 1 - 50 #'s)
    """
    hashcount = '#'
    for i in range(int(anomaly / 0.02)):
      hashcount += '#'
    for j in range(int((1 - anomaly) / 0.02)):
      hashcount += '.'
    return hashcount



class AudioStream:
    
  def __init__(self):
    """
    Instantiate temporal pooler, encoder, audio sampler, filter, & freq plot
    """
    self.vis = Visualizations()

    """
    The number of columns in the input and therefore the TP
     2**9 = 512
     sparsity initial 0.10
     Trial and error pulled that out
     numCols should be tested during benchmarking
    """
    self.numCols = 2**9
    sparsity = 0.03
    self.numInput = int(self.numCols * sparsity)

    """
    Create a bit map encoder

    From the encoder's __init__ method:
     1st arg: the total bits in input
     2nd arg: the number of bits used to encode each input bit
    """
    self.e = SparsePassThroughEncoder(self.numCols, 1)

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
    

    """
    The call to create the temporal pooler region
    """
    self.tp = TP(numberOfCols=self.numCols,
      cellsPerColumn =4,
      initialPerm    =0.5,
      connectedPerm  =0.5,
      minThreshold   =10,
      newSynapseCount=10,
      permanenceInc  =0.1,
      permanenceDec  =0.07,
      activationThreshold=8,
      globalDecay    =0.02,
      burnIn         =2,
      checkSynapseConsistency=False,
      pamLength      =100)


    #initialise anomaly
    self.anomaly = 0
    self.anomalyGrad = 127;

    """
    Print out the inputs
    """
    print "Number of columns:\t" + str(self.numCols)
    print "Max size of input:\t" + str(self.numInput)
    print "Sampling rate (Hz):\t" + str(rate)
    print "Passband filter (Hz):\t" + str(highHertz) + " - " + str(lowHertz)
    print "Passband filter (bin):\t" + str(self.highpass) + " - " + str(self.lowpass)
    print "Bin difference:\t\t" + str(self.lowpass - self.highpass)
    print "Hz per Bin:\t\t" + str(rate/self.buffersize)
    print "Buffersize:\t\t" + str(self.buffersize)
    
    """
    Setup the plot
     Use the bandpass filter frequency range as the x-axis
     Rescale the y-axis
    """
    bin = range(self.highpass,self.lowpass)
    xs = numpy.arange(len(bin))*rate/self.buffersize + highHertz
  
    plt.ion()         #interactive mode on
    
    self.xAxis = 500  #Width of plt. 
    
    plt.subplot(311)  #firs location of a 2 x 1 plots gri - Frequency Spectrum
    self.freqPlot = plt.plot(xs,xs,'r')[0] 
    plt.ylim(0,100000)
  
    plt.subplot(312)  #second plot - Time Signal Scroll. 
    self.timePlot = plt.plot(range(0,self.xAxis),range(0,self.xAxis),'g')[0]
    plt.ylim(-10000,10000)

    plt.subplot(313)  #location of next plot - Anomaly Scroll. 
    self.anomalyPlot = plt.plot(range(0,self.xAxis),range(0,self.xAxis),'b')[0]
    plt.ylim(-10,300.0)
       
  
    """
    Initialise deque arrays to append anomaly and audio values to
    """
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
    Start the Main Thread Loop.
    """
    self.counterTime = 0
    print("Start of Audio Process")
    while True:
      try:
        
        self.processAudio()

      except KeyboardInterrupt:
        
        self.inStream.stop_stream() #PyAudio
        self.inStream.close()       #PyAudio
        p.terminate()               #PyAudio
        
        plt.close()                 #Matplotlib

        self.flag = 0               #Serial
        dmx.blackout()              #Serial
        dmx.close_serial()          #Serial
        dmx.join()                  #Serial
                 
        print("sys.exit() Exit PyAudio, Matplotlib & Serial")
        sys.exit()
        
  def processAudio (self):
      
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
    fs = numpy.sort(ys.argsort()[-self.numInput:])
    rfs = fs.astype(numpy.float32) / (self.lowpass - self.highpass) * self.numCols
    ufs = numpy.int32(numpy.unique(rfs))
    actualInt = self.e.encode(ufs)
    actual = actualInt.astype(numpy.float32)

    """
    Pass the SDR to the TP
    Collect the prediction SDR from the TP
    Pass the prediction & actual SDRS to the anomaly calculator & array comparer
    Update the frequency plot
    """
    self.tp.compute(actual, enableLearn = True, computeInfOutput = True)
    predictedInt = self.tp.getPredictedState().max(axis=1)
    compare = self.vis.compareArray(actualInt, predictedInt)

    self.anomaly = self.vis.calcAnomaly(actualInt, predictedInt)
    #print "." . join(compare)
    #print self.vis.hashtagAnomaly(self.anomaly)
    
    self.freqPlot.set_ydata(ys)# Plot the Frequency Spectrum

    # Plot the TimeScale of the Audio in a scroll, by shifting to the right and filling last element.
    self.timeAudioValues.rotate(-1)
    self.timeAudioValues[self.xAxis -1] = self.audio[1]
    self.timePlot.set_ydata(self.timeAudioValues)
    
    # Normalize anomaly from 0 to 255, integers only. 
    self.anomaly = int(self.anomaly * 255)

    #Shift anomalyValues array (for scrolling) to the right, and fill the last element with new Anomaly value.
    self.anomalyValues.rotate(-1)    
    self.anomalyValues[xAxis-1] =  self.anomaly
    # 4 pole moving average, so smooth changes in Anomaly values
    self.anomalyValues[xAxis-1] =  (self.anomalyValues[xAxis-1] + self.anomalyValues[xAxis-2]] + self.anomalyValues[xAxis-3]] + self.anomalyValues[xAxis-4]])/4
    self.anomalyPlot.set_ydata(self.anomalyValues)

    #print "Value of Anomaly: " + str(self.anomalyValues[xAxis-1])
    
    self.counterTime += 1
    #Update only every 200 times
    if (self.counterTime > 10):    
        plt.show(block = False)
        plt.draw()
        self.counterTime = 0

    #Pass anomaly value to the DMX Thread.
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
        self.RECEIVED_DMX_LABEL	                = 5
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
            #self.ser = serial.Serial(port=port_number, baudrate=57600, timeout=1)
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

    def dmx_test(self, start=1, finish=512):
        print "dmx_usb.dmx_test: Starting DMX test"
        print "dmx_usb.dmx_test: Testing range " + str(start) + " to " + str(finish)
        for i in range(start, finish):
            print "dmx_usb.dmx_test: Test channel " + str(i)
            self.set_channel(i, 100)
            time.sleep(1)
            self.set_channel(i, 0)
        print "dmx_usb.dmx_test: Test Complete!"
        print "dmx_usb.dmx_test: Tested " + str(finish-start+1) + " channels, from " +str(start)+ " to " + str(finish)

    def blackout(self):
        print "DMX Blackout"
        self.channels = [0 for i in range(512)]
        self.update_channels()

    def run(self):
        print "Run DMX Task"
        print "  self.blackout()"
        self.blackout()
        print

        while (self.flag == 1):
            
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



