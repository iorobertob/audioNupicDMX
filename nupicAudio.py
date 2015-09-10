#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
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
pyplot - to plot the sound frequencies
os - to have priority
bitmaparray - encodes an array of indices into an SDR
TP10X2 - the C++ optimized temporal pooler (TP)
"""
import numpy
import pyaudio
import matplotlib.pyplot as plt
import os
from nupic.encoders.sparse_pass_through_encoder import SparsePassThroughEncoder
from nupic.research.TP10X2 import TP10X2 as TP

os.nice(100);

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
     Trial and error pulled that out
     numCols should be tested during benchmarking
    """
    self.numCols = 2**9
    sparsity = 0.10
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
     rate: The sampling rate in Hz of SYBA USB C Media soundcard
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
    The call to create the temporal pooler region
    """
    self.tp = TP(numberOfCols=self.numCols, cellsPerColumn=4,
      initialPerm=0.5, connectedPerm=0.5,
      minThreshold=10, newSynapseCount=10,
      permanenceInc=0.1, permanenceDec=0.07,
      activationThreshold=8,
      globalDecay=0.02, burnIn=2,
      checkSynapseConsistency=False,
      pamLength=100)
  
    """
    Creating the audio stream from our mic
    """
    p = pyaudio.PyAudio()
    WIDTH = 2
    
    def callback(in_data,frame_count, time_info, status):
        self.audio = numpy.fromstring(in_data,dtype=numpy.int16)
        return (self.audio, pyaudio.paContinue)
      
    self.inStream = p.open(format = p.get_format_from_width(WIDTH, unsigned=False),
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
    Print out the inputs
    """
    print "Number of columns:\t" + str(self.numCols)
    print "Max size of input:\t" + str(self.numInput)
    print "Sampling rate (Hz):\t" + str(rate)
    print "Passband filter (Hz):\t" + str(highHertz) + " - " + str(lowHertz)
    print "Passband filter (bin):\t" + str(self.highpass) + " - " + str(self.lowpass)
    print "Bin difference:\t\t" + str(self.lowpass - self.highpass)
    print "Buffersize:\t\t" + str(self.buffersize)

    """
    Setup the plot
     Use the bandpass filter frequency range as the x-axis
     Rescale the y-axis
    """
    plt.ion()
    bin = range(self.highpass,self.lowpass)
    xs = numpy.arange(len(bin))*rate/self.buffersize + highHertz
    self.freqPlot = plt.plot(xs,xs)[0]
    plt.ylim(0, 500000)

    self.inStream.start_stream()
    
    while True:
      try:
        self.processAudio()

      except KeyboardInterrupt:
        
        self.inStream.stop_stream()
        self.inStream.close()      
        p.terminate()        
        plt.close()
        print("* Killed Audio Stream")
        quit()
        pass
  
  
  def processAudio (self): 

    
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
    anomaly = self.vis.calcAnomaly(actualInt, predictedInt)
    print "." . join(compare)
    print self.vis.hashtagAnomaly(anomaly)
    self.freqPlot.set_ydata(ys)
    plt.show(block = False)
    plt.draw()
  
  
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
     (they're the complex conjugates) ' does not matter because we take a section using the bandpass
    Use just the first half to apply the bandpass filter

    Great info here: http://stackoverflow.com/questions/4364823/how-to-get-frequency-from-fft-result
    """
    left = numpy.abs(numpy.fft.fft(audio))
    output = left[highpass:lowpass]
    return output 



audiostream = AudioStream()
