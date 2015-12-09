#-----------------------------------------------------------------------
# Name:        nupicAudioDMX
# Purpose:
#
# Author:      IO - Code
#
# Created:     23/11/2015
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
"""
import numpy 
import math
import random
import pyaudio
import wave
import os
import time
import sys
import optparse
import serial
import threading
import ttk
import glob#The glob module finds all the pathnames matching a specified pattern
from Tkinter import *
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.pyplot   import *

from nupic.frameworks.opf.modelfactory             import ModelFactory # to create the nupic model
from nupic.algorithms.anomaly_likelihood           import AnomalyLikelihood

import model_params     #this has to by a python file in the same folder

def destroy(e): sys.exit() # exit from the GUI
os.nice(100)
########################################################################################################
########################################################################################################
""" Parse for Verbose """
verbose = False
parser = optparse.OptionParser()    
parser.add_option(
    '-v', 
    '--verbose',
    action = "store_true",
    default= False,
    dest   = "verbose",
    help   = "Prints for development purposes")
(options, args) = parser.parse_args()
verbose = options.verbose
########################################################################################################
########################################################################################################
"""
C O N T R O L S
"""
VERBOSE             = 1
ANOMALY_THRESHOLD   = 0.9   # To report when an anomaly exceeds a value. Not implemented.
#-------------------------------------------------------------------------------------------------------
AUDIO               = 1     # Audio module ON/OFF
SR                  = 8000  # Sample Rate of the audio input. 
BITRES              = 16    # Bit Resolution 
BUFFERSIZE          = 2**6  #127
FREQPERBIN          =  int(SR/BUFFERSIZE)   # Frequencies in each bin of the FFT
NOBINS              = 4     # How many frequencies to use for the models
INDEXES             = [
int(500/FREQPERBIN),
int(1000/FREQPERBIN),
int(2000/FREQPERBIN),
int(3000/FREQPERBIN),
]                           # The idexes of the FFT array what has the frequencies of interest. 
FREQS               = 4
GATE                = 40    # Noise Gate Threshold
#-------------------------------------------------------------------------------------------------------
FILES               = 1     # PLAY WAV FILES 
WAV_FILES           = []    # Empty array to later hold the names of the wav files. 
WAV_MINUTES         = 0.01  # The minutes in between triggering the wav files.
#-------------------------------------------------------------------------------------------------------
HTM                 = 1     # HTM   module ON/OFF
HTMHERTZ            = 10    # Model computes per second
#-------------------------------------------------------------------------------------------------------
DMX                 = 1     # DMX   module ON/OFF
SERIAL_PORT         = ''    # Serial port the DMX is connected to
DMX_GAP             = 7     # Space between first address from fixture to fixture
DMX_NUMBER          = 6     # Number of fixtures to use.
DMX_OFFSET          = 1     # Channel number of RED in each Fixture
CYCLE               = 0     # CYCLE+R, CYCLE+G, CYCLE+G, CYCLE increments and wraps around 255
RGB                 = [0] * DMX_GAP * 3    # Array to hold RGB values
BRIGHTENESS         = 1.0   # Range[0.0,1.0]
#-------------------------------------------------------------------------------------------------------
PLOT                = 0     # Plot  module ON/OFF
#-------------------------------------------------------------------------------------------------------
START               = 0     # Start the execution of the secondary Thread after the Tkinter
MODEL_RUN           = 1     # Start the processing loop
PAUSE               = 1     # Pause the processing loop
#######################################################################################################
#######################################################################################################

print"Running... Press Ctrl+Z to force close"

class interface:

    def __init__(self):
        nupicAudioDMX = Main() #4 bins 
        nupicAudioDMX.start()

        def gateControl(*args):
            global GATE 
            GATE = int(entryGATE.get())
            print "Noise Gate set to " + str(entryGATE.get()) + " dB"

        def setBright(*args):
            global BRIGHTENESS
            BRIGHTENESS = float(entryDMXBRIGHT.get())
            print "Brightness: " + str(BRIGHTENESS)

        def on_closing():
            global MODEL_RUN
            global PAUSE
            print 'Stop'
            PAUSE       = 0
            MODEL_RUN   = 0
            root.destroy()
            sys.exit()

        def stopProgram(*args):
            global MODEL_RUN
            global PAUSE
            print 'Stop '
            PAUSE       = 0
            MODEL_RUN   = 0

        def pauseProgram(*args):
            print'Pause'
            global PAUSE
            PAUSE       = 0

        def startProgram(*args):
            global model_params
                      
            global PLOT     

            global HTM
            global NOBINS

            global AUDIO
            global FILES
            global WAV_FILES
            global WAV_MINUTES
            global SR
            global FREQS                 
            global START
            global PAUSE
            global INDEXES

            global DMX
            global SERIAL_PORT
            global DMX_NUMBER
            global DMX_GAP
            global DMX_OFFSET
            global RGB
            global BRIGHTNESS

            AUDIO       =             audioVar.get()
            SR          =          int(entrySR.get())
            FILES       =             filesVar.get()
            noFiles     =    int(entryFILESNUM.get())
            WAV_FILES   = [(str(i+1)+'.wav') for i in range(noFiles)] 
            WAV_MINUTES =     float(entryWAVMINS.get())           

            HTM         =               htmVar.get()
            NOBINS      =    int(entryMODELNUM.get())
            HTMHERTZ    =    int(entryHTMHERTZ.get())
            model_params.MODEL_PARAMS['modelParams']['spParams']['columnCount']    = int(entryCOLUMNS.get())
            model_params.MODEL_PARAMS['modelParams']['tpParams']['columnCount']    = int(entryCOLUMNS.get())
            model_params.MODEL_PARAMS['modelParams']['tpParams']['cellsPerColumn'] = int(  entryCELLS.get())            

            DMX         =               dmxVar.get()
            SERIAL_PORT =            serialVar.get()
            DMX_NUMBER  =      int(entryDMXNUM.get())
            DMX_GAP     =      int(entryDMXGAP.get())
            DMX_OFFSET  =    int(entryDMXOFFST.get())
            BRIGHTNESS  = float(entryDMXBRIGHT.get()) 

            PLOT        =              plotVar.get()
            
            for i in range(len(entryFREQS)):
                INDEXES[i] = int(int(entryFREQS[i].get())/FREQPERBIN )               

            for i in range(len(entryRGB)):
                RGB[i] = int(entryRGB[i].get())                

            START   = 1
            PAUSE   = 1
            print 'Start'
            print 'Frequencies to Analyse:'
            print entryFREQS[0].get() + " Hz, " + entryFREQS[1].get() + " Hz, " + entryFREQS[2].get() + " Hz, and " + entryFREQS[3].get() + " Hz."
        """-----------------------------------------------------------------------------------------------------------------------------"""
                            
        """ Start building the interface - Variables """              
        winX        = 700
        winY        = 350
        rowHeight   = 25
        columns     = 3        
        space       = 10
        leftMargin  = 20
        width       = (winX-(2*leftMargin))/(2*columns)

        root = Tk()
        root.title("Audio NuPIC DMX")
        root.geometry("700x400")
        """-----------------------------------------------------------------------------------------------------------------------------"""

        """ Variables for Checkboxes  """
        dmxVar      = IntVar()
        audioVar    = IntVar()
        filesVar    = IntVar()
        plotVar     = IntVar()
        htmVar      = IntVar()
        dmxVar.set(  1)
        audioVar.set(1)
        filesVar.set(1)
        plotVar.set( 0)
        htmVar.set(  1)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Entry Objects and their Position"""

        entryFREQS = [Entry(root) for i in range(FREQS)] 
        entryRGB   = [Entry(root) for i in range(3*DMX_NUMBER)]     

        entryGATE       = Entry(root)
        entrySR         = Entry(root)
        entryFILESNUM   = Entry(root)
        entryWAVMINS    = Entry(root)
        entryFREQNUM    = Entry(root) 
        entryMODELNUM   = Entry(root) 
        entryCOLUMNS    = Entry(root) 
        entryCELLS      = Entry(root)
        entryHTMHERTZ   = Entry(root)
        entryDMXNUM     = Entry(root)
        entryDMXGAP     = Entry(root) 
        entryDMXOFFST   = Entry(root)  
        entryDMXBRIGHT  = Entry(root)      
        
        entryFREQS[0].place( x=leftMargin+1.5*width,                     y=(2*rowHeight)+(1*space), width=width/2,   height=rowHeight)
        entryFREQS[1].place( x=leftMargin+1.5*width,                     y=(3*rowHeight)+(2*space), width=width/2,   height=rowHeight)
        entryFREQS[2].place( x=leftMargin+1.5*width,                     y=(4*rowHeight)+(3*space), width=width/2,   height=rowHeight)
        entryFREQS[3].place( x=leftMargin+1.5*width,                     y=(5*rowHeight)+(4*space), width=width/2,   height=rowHeight)

        entryGATE.place(     x=leftMargin,                               y=(5*rowHeight)+(4*space), width=width/4,   height=rowHeight) 
        entrySR.place(       x=leftMargin+width/2,                       y=(3*rowHeight)+(2*space), width=width/2,   height=rowHeight)
        entryFILESNUM.place( x=leftMargin+width*2/3,                     y=(8*rowHeight)+(7*space), width=width/3,   height=rowHeight)
        entryWAVMINS.place(  x=leftMargin+width*2/3,                     y=(9*rowHeight)+(8*space), width=width/3,   height=rowHeight)  
        entryMODELNUM.place( x=leftMargin+(2*width)+width,               y=(3*rowHeight)+(2*space), width=width/2,   height=rowHeight)  
        entryCOLUMNS.place(  x=leftMargin+(2*width)+width,               y=(4*rowHeight)+(3*space), width=width/2,   height=rowHeight)  
        entryCELLS.place(    x=leftMargin+(2*width)+width,               y=(5*rowHeight)+(4*space), width=width/2,   height=rowHeight)
        entryHTMHERTZ.place( x=leftMargin+(2*width)+width,               y=(6*rowHeight)+(5*space), width=width/2,   height=rowHeight)  
        entryDMXNUM.place(   x=leftMargin+(4.5*width),                   y=(3*rowHeight)+(2*space), width=width/4,   height=rowHeight)
        entryDMXGAP.place(   x=leftMargin+(5*width),                     y=(7*rowHeight)+(6*space), width=width/2,   height=rowHeight) 
        entryDMXOFFST.place( x=leftMargin+(5*width),                     y=(8*rowHeight)+(7*space), width=width/2,   height=rowHeight)
        entryDMXBRIGHT.place(x=leftMargin+(5*width),                     y=(9*rowHeight)+(8*space), width=width/2,   height=rowHeight)   
        entryRGB[0].place(   x=leftMargin+(4*width)+0*(width/3-3)      , y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight)
        entryRGB[1].place(   x=leftMargin+(4*width)+1*(width/3-3)      , y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight)
        entryRGB[2].place(   x=leftMargin+(4*width)+2*(width/3-3)      , y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight)
        entryRGB[3].place(   x=leftMargin+(4*width)+0*(width/3-3)      , y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight)
        entryRGB[4].place(   x=leftMargin+(4*width)+1*(width/3-3)      , y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight)
        entryRGB[5].place(   x=leftMargin+(4*width)+2*(width/3-3)      , y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight)
        entryRGB[6].place(   x=leftMargin+(4*width)+3*(width/3-3)+space, y=(2*rowHeight)+(1*space), width=width/3-3, height=rowHeight)               
        entryRGB[7].place(   x=leftMargin+(4*width)+4*(width/3-3)+space, y=(2*rowHeight)+(1*space), width=width/3-3, height=rowHeight) 
        entryRGB[8].place(   x=leftMargin+(4*width)+5*(width/3-3)+space, y=(2*rowHeight)+(1*space), width=width/3-3, height=rowHeight)
        entryRGB[9].place(   x=leftMargin+(4*width)+3*(width/3-3)+space, y=(3*rowHeight)+(2*space), width=width/3-3, height=rowHeight) 
        entryRGB[10].place(  x=leftMargin+(4*width)+4*(width/3-3)+space, y=(3*rowHeight)+(2*space), width=width/3-3, height=rowHeight) 
        entryRGB[11].place(  x=leftMargin+(4*width)+5*(width/3-3)+space, y=(3*rowHeight)+(2*space), width=width/3-3, height=rowHeight) 
        entryRGB[12].place(  x=leftMargin+(4*width)+3*(width/3-3)+space, y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight) 
        entryRGB[13].place(  x=leftMargin+(4*width)+4*(width/3-3)+space, y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight) 
        entryRGB[14].place(  x=leftMargin+(4*width)+5*(width/3-3)+space, y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight) 
        entryRGB[15].place(  x=leftMargin+(4*width)+3*(width/3-3)+space, y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight) 
        entryRGB[16].place(  x=leftMargin+(4*width)+4*(width/3-3)+space, y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight) 
        entryRGB[17].place(  x=leftMargin+(4*width)+5*(width/3-3)+space, y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight) 

        entryFREQS[0].insert(END, INDEXES[0])        
        entryFREQS[1].insert(END, INDEXES[1])   
        entryFREQS[2].insert(END, INDEXES[2])            
        entryFREQS[3].insert(END, INDEXES[3])

        entryGATE.insert(    END, 40)   
        entrySR.insert(      END, SR)
        entryFILESNUM.insert(END, 2) 
        entryWAVMINS.insert( END, 5)       
        entryMODELNUM.insert(END, 4)      
        entryCOLUMNS.insert( END, 2048)  
        entryCELLS.insert(   END, 32)
        entryHTMHERTZ.insert(END, HTMHERTZ)     
        entryDMXNUM.insert(  END, DMX_NUMBER)
        entryDMXGAP.insert(  END, DMX_GAP)
        entryDMXOFFST.insert(END, DMX_OFFSET)
        entryDMXBRIGHT.insert(END,BRIGHTENESS) 

        entryRGB[0].insert(END, 255)        
        entryRGB[1].insert(END, 80) # RED        
        entryRGB[2].insert(END, 80)

        entryRGB[3].insert(END, 255)   
        entryRGB[4].insert(END, 255)# YELLOW   
        entryRGB[5].insert(END, 0)

        entryRGB[6].insert(END, 255)   
        entryRGB[7].insert(END, 153) # ORANGE  
        entryRGB[8].insert(END, 51)

        entryRGB[9].insert(END, 51)   
        entryRGB[10].insert(END, 204) # GREEN  
        entryRGB[11].insert(END, 51)

        entryRGB[12].insert(END, 51)   
        entryRGB[13].insert(END, 102) # BLUE  
        entryRGB[14].insert(END, 255)

        entryRGB[15].insert(END, 204)   
        entryRGB[16].insert(END, 0)   # PURPLE
        entryRGB[17].insert(END, 255) 
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Label Objects and their position """

        ttk.Label(root, text="CONTROL",).place(x=leftMargin,                   y=rowHeight,       width=winX-(leftMargin*2), height=rowHeight)
        ttk.Label(root, text="Freq. 1" ).place(x=leftMargin+width,             y=(2*rowHeight)+(1*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Freq. 2" ).place(x=leftMargin+width,             y=(3*rowHeight)+(2*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Freq. 3" ).place(x=leftMargin+width,             y=(4*rowHeight)+(3*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Freq. 4" ).place(x=leftMargin+width,             y=(5*rowHeight)+(4*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Hz"      ).place(x=leftMargin+2*width,           y=(2*rowHeight)+(1*space), width=width/4,     height=rowHeight)
        ttk.Label(root, text="Hz"      ).place(x=leftMargin+2*width,           y=(3*rowHeight)+(2*space), width=width/4,     height=rowHeight)
        ttk.Label(root, text="Hz"      ).place(x=leftMargin+2*width,           y=(4*rowHeight)+(3*space), width=width/4,     height=rowHeight)
        ttk.Label(root, text="Hz"      ).place(x=leftMargin+2*width,           y=(5*rowHeight)+(4*space), width=width/4,     height=rowHeight)
        ttk.Label(root, text="dB"      ).place(x=leftMargin+(width/4),         y=(5*rowHeight)+(4*space), width=width/4,     height=rowHeight)
        ttk.Label(root, text="Audio"   ).place(x=leftMargin+(0*2*width),       y=(2*rowHeight)+(1*space), width=width-space, height=rowHeight)
        ttk.Label(root, text="S R"     ).place(x=leftMargin,                   y=(3*rowHeight)+(2*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Audio Files").place(x=leftMargin,                y=(7*rowHeight)+(6*space), width=width,       height=rowHeight)
        ttk.Label(root, text="Number"  ).place(x=leftMargin,                   y=(8*rowHeight)+(7*space), width=2*width/3,   height=rowHeight)
        ttk.Label(root, text="Interval").place(x=leftMargin,                   y=(9*rowHeight)+(8*space), width=2*width/3,   height=rowHeight)
        ttk.Label(root, text="HTM"     ).place(x=leftMargin+(2*width)+width/2, y=(2*rowHeight)+(1*space), width=width,       height=rowHeight)
        ttk.Label(root, text="Models"  ).place(x=leftMargin+(2*width)+width/2, y=(3*rowHeight)+(2*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Cols."   ).place(x=leftMargin+(2*width)+width/2, y=(4*rowHeight)+(3*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Cells"   ).place(x=leftMargin+(2*width)+width/2, y=(5*rowHeight)+(4*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Hertz"   ).place(x=leftMargin+(2*width)+width/2, y=(6*rowHeight)+(5*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="DMX"     ).place(x=leftMargin+(4*width),         y=(2*rowHeight)+(1*space), width=width-space, height=rowHeight)
        ttk.Label(root, text="Chls."   ).place(x=leftMargin+(4*width),         y=(3*rowHeight)+(2*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="DMX Gap" ).place(     x=leftMargin+(4*width),    y=(7*rowHeight)+(6*space), width=width-3,     height=rowHeight)
        ttk.Label(root, text="First Channel").place(x=leftMargin+(4*width),    y=(8*rowHeight)+(7*space), width=width-3,     height=rowHeight)
        ttk.Label(root, text='Brightness').place(   x=leftMargin+(4*width),    y=(9*rowHeight)+(8*space), width=width-3,     height=rowHeight)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Button Objects and their position  """

        ttk.Button(root, text="Start", command=startProgram).place(x=leftMargin+4*width,           y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text="Pause", command=pauseProgram).place(x=leftMargin+4*width+2*width/3, y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text="Stop",  command=stopProgram ).place(x=leftMargin+4*width+4*width/3, y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text='Set',   command=setBright   ).place(x=leftMargin+(5.5*width),       y=(9*rowHeight)+(8*space),  width=width/2-5,   height=rowHeight)
        ttk.Button(root, text="Gate",  command =gateControl).place(x=leftMargin+(width/2),         y=(5*rowHeight)+(4*space),  width=width/2,     height=rowHeight)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Checkbutton Objects and their position """

        ttk.Checkbutton(root, variable=dmxVar  ).place(x=leftMargin+(4*width)+2*(width/3-3),   y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=audioVar).place(x=leftMargin+(0.75*width) ,             y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=filesVar).place(x=leftMargin+(0.75*width) ,             y=(7*rowHeight)+(6*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=htmVar  ).place(x=leftMargin+(2*1*width)+1.25*width ,   y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ OptionMenu Object """

        ports = glob.glob('/dev/tty.*')         
        serialVar = StringVar()
        omSERIALPORT = ttk.OptionMenu(root, serialVar, ports[0], *ports)
        omSERIALPORT.place(x=leftMargin+(2*2*width), y=(6*rowHeight)+(5*space),width=2*width, height=rowHeight     )
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Start the GUI """

        root.bind('<Return>', startProgram)
        root.protocol("WM_DELETE_WINDOW",on_closing)
        root.mainloop()
        """-----------------------------------------------------------------------------------------------------------------------------"""


class nupicModels(threading.Thread):
    """
    NuPIC models - One instance created per frequency bin to analise in this project
    """
    
    def __init__(self, number, HTMHERTZ):

        threading.Thread.__init__(self)
        self.daemon = True

        # Flags and logic 
        self.HTM        = 1
        self.HTMHERTZ   = HTMHERTZ
        self.number     = number

        # Create model, set the predicted field, run and get anomaly
        self.amplitude  = 1
        self.model      = ModelFactory.create(model_params.MODEL_PARAMS)
        self.model.enableInference({'predictedField': 'binAmplitude'})
        self.likelihoods= AnomalyLikelihood()

        self.result     = self.model.run({"binAmplitude" : 0})
        self.anomaly    = self.result.inferences['anomalyScore']    
        self.likelihood = self.likelihoods.anomalyProbability(0, 0) 

    
    def run(self): 

        self.startTime = time.time()
        
        while self.HTM:
            """ Continuous Execution""" 
            if time.time()-self.startTime > 1/self.HTMHERTZ:
                self.result     = self.model.run({"binAmplitude" : self.amplitude})
                self.anomaly    = self.result.inferences['anomalyScore']    
                self.likelihood = self.likelihoods.anomalyProbability(self.amplitude, self.anomaly) 
                if verbose:
                    print 'Anomaly Thread '    + str(self.number) + ": " + str(self.anomaly)
                    print 'Time taken Thread ' + str(self.number) + ': ' + format(time.time() - self.startTime)           
                self.startTime = time.time()

        self.HTM = 0
        print"End of Nupic Model " + str(self.number)
            

class Visualizations(threading.Thread):
    
    def __init__(self, xAxis, freqPerBin, noBins, indexes):

        threading.Thread.__init__(self)
        self.daemon = True

        """
        Initialise constants, variables and buffers
        """
        self.PLOT               = 1
        self.FREQPERBIN         = freqPerBin
        self.NOBINS             = noBins    # Number of bins Windos is split into
        self.INDEXES            = indexes   # List of indexes of bins of interest, see bottom        
        self.xAxis              = xAxis     # Width of plot

        self.binValues          = []        # 2D: xAxis samples by NOBINS bins to plot (i.e. 200x4) - 4 lines in a plot 
        self.anomalyValues      = []        # 2D: xAxis anomaly samples by NOBINS bins' anomalies to plot (i.e. 200x4) - 4 lines in a plot 
        self.likelihoodValues   = []        # 2D: xAxis likelihood samples by NOBINS bins to plot (i.e. 200x4) - 4 lines in a plot 

        self.anomalyAv          = 0         # Averate of Normalised Anomalies Average. Still a float value
        self.likelihoodAv       = 0         # Average of Normalised Likelihoods Average. Still a float value.
        self.counterTime        = 0         # Counter to delay by some loops


        """
        Initialise deque arrays to append anomaly and audio values to. Use deque high performance holders
        """
        for i in range(self.NOBINS):
            print 1   
            self.binValues.append       ( deque([0.0]*self.xAxis,maxlen=self.xAxis))#To hold a frequency bin values over time.
            self.anomalyValues.append   ( deque([0.0]*self.xAxis,maxlen=self.xAxis))#Buffer to hold anomaly values
            self.likelihoodValues.append( deque([0.0]*self.xAxis,maxlen=self.xAxis))#Buffer to hold likelihood values
       
        self.timeAudioValues            = deque([0.0]*self.xAxis,maxlen=self.xAxis) # To hold time audio values and display them.
        self.anomalyAverage             = deque([0.0]*self.xAxis,maxlen=self.xAxis) # To hold anomalies averages and plot
        self.likelihoodAverage          = deque([0.0]*self.xAxis,maxlen=self.xAxis) # To hold likelihoods averages and plot
       
        print 2
        """
        Interactive mode on
        """
        plt.ion()
        print 3
    
        """
        Creating 3 subplots with xAxis width
        """
        plt.subplot(111)  #firs location of a 2 x 1 plots grid - Frequency Spectrum
        print 3.5
        self.freqPlot = plt.plot(range(self.xAxis),range(self.xAxis),'r',label="Frequency Spectrum")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        print 4
        plt.subplot(412)  #second plot - Time Signal Scroll.
        self.timePlot = plt.plot(range(self.xAxis),range(self.xAxis),'g', label="Time Audio")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(-10000,10000)

        plt.subplot(413)  #location of next plot - Anomaly Scroll.
        self.anomalyPlot = plt.plot(range(self.xAxis),range(self.xAxis),'b', label="Anomaly in Time")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(-10,300.0)

        plt.subplot(414)  #location of next plot - Anomaly Scroll.
        self.anomalyPlot = plt.plot(range(self.xAxis),range(self.xAxis),'b', label="Anomaly Likelihood in Time")[0]
        plt.legend(bbox_to_anchor=(0.5, 0.75, 0.5, .1), loc=3, mode="expand", borderaxespad=0.)
        plt.ylim(-10,300.0)

        # Ready to plot
        self.plottingFlag = 0
        print 'final init'


    def setVars(self, audio, audioFFT,anomaly, likelihood):
            
            if (self.plottingFlag == 0):
                self.audioFFT       = audioFFT   
                self.audio          = audio
                self.anomalyVis     = anomaly   
                self.likelihood     = likelihood
                self.plottingFlag   = 0


    def run(self):
        
        
        while self.PLOT:
            
            if (self.plottingFlag == 1):    

                """
                Plot - Amplitude of the Frequency Bin, or Bins as scroll, shift vector and insert value at end, then plot.
                """
                plt.subplot(411)  #Four plots, 1 column first item 
                plt.cla()

                for i in range(0,self.NOBINS):
                    self.binValues[i].rotate(-1)
                    self.binValues[i][self.xAxis-1] = self.audioFFT[self.INDEXES[i]] 
                    plt.plot(self.binValues[i], label = "" + str((self.INDEXES[i]) * self.FREQPERBIN) + "Hz")

                plt.ylim(50,150)
                plt.legend(bbox_to_anchor=(0.6, 0.75, 0.4, .1), loc=3, ncol=self.NOBINS,mode="expand", borderaxespad=0.0)
                
                
                """
                Plot - Amplitude of the Audio Signal as scroll, shift vector and insert value at end, then plot.
                """
                self.timeAudioValues.rotate(-1)
                self.timeAudioValues[self.xAxis -1] = self.audio[1]
                self.timePlot.set_ydata(self.timeAudioValues)                                                       
                  
                """
                Plot - Anomaly Value as scroll, shift vector and insert value at end, then plot. Comb filter could go out of this thread
                """ 
                plt.subplot(413)  #Four plots, 1 column, third item 
                plt.cla()
                self.anomalyAverage.rotate(-1)
                self.anomalyAverage[self.xAxis-1] = self.anomalyAv

                for i in range(self.NOBINS):

                    self.anomalyValues[i].rotate(-1)
                    self.anomalyValues[i][self.xAxis-1] = self.anomalyVis[i]
                    #### Comb Filter ###############################################################################################
                    # self.anomalyValues[i][self.xAxis-1] = (self.anomalyValues[i][self.xAxis-1] + self.anomalyValues[i][self.xAxis-2] 
                    #     + self.anomalyValues[i][self.xAxis-3] + self.anomalyValues[i][self.xAxis-4])/4
                    ################################################################################################################
                    plt.plot(self.anomalyValues[i], label = "Anly. " + str(i)) 
                                
                plt.plot(self.anomalyAverage, label = 'Avrg')
                plt.ylim(0,1.0)
                plt.legend(bbox_to_anchor=(0.4, 0.75, 0.6, .1), loc=3, ncol=self.NOBINS+1,mode="expand", borderaxespad=0.)  

                                                                   
                """
                Plot the Anomaly Likelihood Value as scroll, shift vector and insert value at end, then plot. TODO. Take Comb filter out of thread
                """ 
                plt.subplot(414)  #firs location of a 2 x 1 plots grid - Frequency Spectrum
                plt.cla()
                self.likelihoodAverage.rotate(-1)
                self.likelihoodAverage[self.xAxis-1] = self.likelihoodAv

                for i in range(self.NOBINS):

                    self.likelihoodValues[i].rotate(-1)
                    self.likelihoodValues[i][self.xAxis-1] = self.likelihood[i]##numpy.random_sample()*255
                    #### Comb Filter ###############################################################################################
                    # self.likelihoodValues[i][self.xAxis-1] = (self.likelihoodValues[i][self.xAxis-1] + self.likelihoodValues[i][self.xAxis-2] 
                    #     + self.likelihoodValues[i][self.xAxis-3] + self.likelihoodValues[i][self.xAxis-4])/4
                    ################################################################################################################
                    plt.plot(self.likelihoodValues[i], label = "Lklhd. " + str(i)) 
                
                plt.plot(self.likelihoodAverage, label = 'Avrg')
                plt.ylim(0,1.0)
                plt.legend(bbox_to_anchor=(0.4, 0.75, 0.6, .1), loc=3, ncol=self.NOBINS+1,mode="expand", borderaxespad=0.) 
                                           
                plt.show(block = False)
                plt.draw()                

                self.plottingFlag = 0
        plt.close()
        self.PLOT = 0


class AudioStream:

    def __init__(self, sr, bufferSize, bitRes):

        self.daemon = True

        """
        Sampling details
        rate: The sampling rate in Hz of my soundcard
        sizeBuffer: The size of the array to which we will save audio segments (2^12 = 4096 is very good)
        """
        self.audioStarted   = 0
        self.rate           = sr
        self.bufferSize     = bufferSize
        self.bitRes         = bitRes 
        self.binSize        =int(self.rate/self.bufferSize)
        if (self.bitRes == 16):
            width = 2
        if (self.bitRes == 8):
            width = 1
        if (self.bitRes == 32):
            width = 4    

   
        """
        Creting the audio stream from our mic, Callback Mode.
        """
        p = pyaudio.PyAudio()
        

        """
        Setting up the array that will handle the timeseries of audio data from our input
        """
        if (self.bitRes == 16):
            self.audio = numpy.empty((self.bufferSize),dtype="int16")
            print "Using 16 bits"
        if (self.bitRes == 8):
            self.audio = numpy.empty((self.bufferSize),dtype="int8")
            print "Using 8 bits"
        if (self.bitRes == 32):
            self.audio = numpy.empty((self.bufferSize),dtype="int32")
            print "Using 32 bits"


    
        def callback(in_data,frame_count, time_info, status):
            self.audio = numpy.fromstring(in_data,dtype=numpy.int16)
            self.audioFFT = self.fft(self.audio)
            self.audioFFT = 20*numpy.log10(self.audioFFT)         
            self.audioStarted = 1
            return (self.audioFFT, pyaudio.paContinue)

        """
        Open the Audio Stream.
        Start separate thread
        """    
        self.inStream = p.open(format   = p.get_format_from_width(width, unsigned=False),
                               channels =1,
                               rate     =self.rate,
                               input    =True,
                               frames_per_buffer=self.bufferSize,
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


class AudioFile(threading.Thread):
    

    def __init__(self,file):

        threading.Thread.__init__(self)
        self.daemon = True

        # Flags         
        self.play   = 0 
        self.FILES  = 1

        """ Initialise Audio Stream"""
        self.file    = wave.open(file,'rb')
        self.pyAu    = pyaudio.PyAudio()
        self.chunk   = 1024
        self.stream  = self.pyAu.open(
            format   = self.pyAu.get_format_from_width(self.file.getsampwidth()),
            channels = self.file.getnchannels(),
            rate     = self.file.getframerate(),
            output   = True)

    def run(self):
        print 'Start File: '
        while self.FILES:
            if self.play:
                """Play entire file"""
                self.play = 0
                data = self.file.readframes(self.chunk)
                while data != '':
                    self.stream.write(data)
                    data = self.file.readframes(self.chunk)
                self.file.rewind()


    def close(self):
        """Close Stream"""
        self.stream.close()


class PyDMX(threading.Thread):
    """
    D M X  Class for Enttec USB Pro serial porotocol.
    Select the name of the usb port, use baud rate of 57600
    fills an array with the Enteec protocol, 512 channels,
    taking the anomaly value from the Main Thread and using it 
    as chanell value.
    """
    def __init__(self, fixnumber, length, dmxOffset, gap, rgb):
          
        threading.Thread.__init__(self)
        self.daemon     = True
        
        # Flags and Logic
        self.DMX            = 1
        self.FIXTURENUMBER  = fixnumber
        self.CYCLE          = 0
        self.BRIGHTNESS     = 1.0


        # DMX setup and Data
        self.channels   = [0 for i in range(512)]
        self.length     = length 
        self.VALUES     = [0]*self.length
        self.DMX_OFFSET = dmxOffset
        self.DMX_GAP    = gap 
        self.RGB        = rgb

        #----------------------------------------------------------
        
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
            #self.ser = serial.Serial(port="/dev/tty.usbserial-EN169205", baudrate=57600, timeout=1)
            self.ser = serial.Serial(port=SERIAL_PORT, baudrate=57600, timeout=1)
        
        except:
            print "dmx_usb.__init__: ERROR: Could not open %u" % (port_number+1)
        #sys.exit(0)
        else:
            print "DMX: Using %s" % (self.ser.portstr)
    
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

    # Higher level functions:
    def set_channel(self, channel, value=0):
        # Channel = DMX Channel (1-512)
        # Value = Strength (0-100%)
        self.channels[channel] = value

    
    def update_channels(self):
        '''Send all 512 DMX Channels from channels[] to the hardware:
        update_channels()'''
        # This is where the magic happens
        # print "DMX Send Anomaly:" + str(self.VALUES)
        self.int_data = [0] + self.channels
        #print (self.int_data)
        

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
        self.blackout() 
        
        while self.DMX:

            for i in range(self.FIXTURENUMBER):
                for j in range(3):

                    channel = i*self.DMX_GAP+j+self.DMX_OFFSET
                    colour = int((self.RGB[3*i+j] + self.CYCLE)*self.BRIGHTNESS*self.VALUES[int(i - (self.length*math.floor(i/self.length)) ) ])  
                    
                    if colour > 255:
                        colour = int(colour - 255*math.floor(colour/255) )
                    self.set_channel(channel,colour)
                    if verbose:
                        print "Set Channel " + str(channel) + " to " + str(colour)

            
            #Send data to Enttec Device
            self.update_channels()
        
        #Clear Output, set all channels to 0's
        print 'Out of dmx'

        DMX = 0
        self.blackout()
        self.close_serial()
        self.stop()


class Main(threading.Thread):
    
    def __init__(self):

        threading.Thread.__init__(self)
        self.daemon = True
        
    def run(self):
        global AUDIO
        global FILES
        global HTM
        global HTMREADY
        global DMX
        global CYCLE
        global PLOT
        global START        
        global MODEL_RUN
        global PAUSE        
        
        while START == 0:1
        
        """ Create & run AudioStream object """   
        if AUDIO:         
            audioObject = AudioStream(SR, BUFFERSIZE, BITRES)               
            audioObject.inStream.start_stream()
            while (audioObject.audioStarted == 0):1#loop to wait the audio to start
            audio       = audioObject.audio
            audioFFT    = audioObject.audioFFT            
            print 'Start Audio Stream'
            print "Sampling rate (Hz):\t"    + str(SR)
            print "Hz per Bin:\t\t"          + str(SR/BUFFERSIZE)
            print "Buffersize:\t\t"          + str(BUFFERSIZE)
        else:
            audio       = [i for i in range(BUFFERSIZE)]
            audioFFT    = audio

        """Create & run WAV Files"""
        if FILES:
            wavFiles = [AudioFile(WAV_FILES[i]) for i in range(len(WAV_FILES))]
            [wavFiles[i].start() for i in range(len(wavFiles))]
            print 'Loading following audio files: '
            print WAV_FILES
        

        """ Create DMX object, start thread outputs messages from a buffer"""  
        if DMX:
            print 'Start DMX Stream'      
            dmx = PyDMX(DMX_NUMBER, NOBINS, DMX_OFFSET, DMX_GAP, RGB)
            dmx.start()
            

        """ Start the NuPIC model """
        if HTM:
            nupicObject = [nupicModels(i,HTMHERTZ) for i in range(NOBINS)]
            [nupicObject[i].start() for i in range(NOBINS)]                        
            print 'Start NuPIC models'
            print "Number of NuPIC models:\t"+ str(NOBINS) 
        anomaly      = [i for i in range(NOBINS)]
        likelihood   = anomaly
        anomalyAv    = 0.5
        likelihoodAv = 0.5 #Range expanded and clipped for DMX Lighting reasons!


        """ Initialise the plots, BUFFERSIZE is the width of the plot. """
        if PLOT:            
            vis = Visualizations(BUFFERSIZE,FREQPERBIN, NOBINS, INDEXES)
            vis.setVars(audio, audioFFT, anomaly, likelihood)
            vis.start()
            print 'Start MatPlotLib'

      
        """
        Start the Main Thread Loop.
        """
        MODEL_RUN   = 1
        startTime   = time.time()
        elapsed     = startTime
        elapsedHTM  = startTime
        
        while MODEL_RUN:  

            while PAUSE:
                try:

                    """ AUDIO STREAM  - ...      """
                    if AUDIO:
                        audio       = audioObject.audio
                        audioFFT    = audioObject.audioFFT
                    """---------------------------------------------------------------------------------------"""

                    """ NUPIC MODEL - Run the NuPIC model and get the anomaly score back. Feed on bin only."""
                                            
                    if HTM and AUDIO:
                        for i in range(NOBINS):
                            if audioFFT[INDEXES[i]] >= GATE and audioFFT[INDEXES[i]] < 200:
                                nupicObject[i].amplitude    = int(audioFFT[INDEXES[i]])
                            elif audioFFT[INDEXES[i]] < GATE: #GATE!
                                nupicObject[i].amplitude    = 0                        
                        anomaly     = [nupicObject[i].anomaly    for i in range(NOBINS)]
                        likelihood  = [nupicObject[i].likelihood for i in range(NOBINS)]
                        anomalyAv    = numpy.sum(anomaly)   /NOBINS
                        likelihoodAv = numpy.sum(likelihood)/NOBINS #Range expanded and clipped for DMX Lighting reasons!
                        if verbose:
                            print "Anomaly : " + str(anomaly)

                    if HTM and AUDIO == 0:
                        for i in range(NOBINS):
                            nupicObject[i].amplitude    = random.randint(0,200)                                                 
                        anomaly      = [nupicObject[i].anomaly    for i in range(NOBINS)]
                        likelihood   = [nupicObject[i].likelihood for i in range(NOBINS)]
                        anomalyAv    = numpy.sum(anomaly)   /NOBINS
                        likelihoodAv = numpy.sum(likelihood)/NOBINS #Range expanded and clipped for DMX Lighting reasons!
                        if verbose:
                            print "Anomaly no Audio : " + str(anomaly)
                    """---------------------------------------------------------------------------------------"""

                    """ WAV FILES - Play a number of wav files sorted corresponding to the anomaly value """

                    if FILES:
                        if time.time()-elapsed > WAV_MINUTES*60:                        
                            print 'Audio for Anomaly: ' + str(anomalyAv) 
                            wavFiles[int(anomalyAv*(len(wavFiles)))].play = 1

                            elapsed = time.time()
                    """---------------------------------------------------------------------------------------"""

                    """ DMX - Pass Likelihood value to the DMX Thread. Clip values below 0."""
                    if DMX and HTM:
                        if anomalyAv < 0:
                            dmx.VALUES = [0]*NOBINS                   
                        if anomalyAv > 0.17:
                            #dmx.VALUES = int(anomalyAv*255)#CHANGE OR ADD self.anomalyLikelihood
                            dmx.VALUES = anomaly                            
                            #dmx.VALUES = int(likelihoodAv*300 -50)#CHANGE OR ADD self.anomalyLikelihood
                        # Cycle the colour values of the DMX channels, keeping their RGB proportion, and cycling through 255 steps
                        CYCLE += 1
                        if(CYCLE > 255):
                            CYCLE = 0

                    if DMX and HTM == 0:
                        if 1 < audioFFT[10] and  audioFFT[10] < 255:
                            #dmx.VALUES = int(audioObject.ys[10])# Send the audio value as DMX
                            dmx.VALUES = random.randint(0,1)
                        else:
                            dmx.VALUES = 0
                        CYCLE += 1
                        if(CYCLE > 255):
                            CYCLE = 0
                    """---------------------------------------------------------------------------------------"""

                    """ PLOT - Pass values to Plot Thread """
                    if PLOT:
                        vis.anomalyVis      = anomaly
                        vis.likelihood      = likelihood
                        vis.audio           = audio  
                        vis.audioFFT        = audioFFT                  
                        vis.likelihoodAv    = likelihoodAv  
                        vis.anomalyAv       = anomalyAv            
                        vis.plottingFlag    = 1   
                    """---------------------------------------------------------------------------------------"""   

                    """ Main metrics """
                    if verbose:
                        print 'Time taken in main Loop: ' + format(time.time() - startTime) 

                    startTime = time.time()
                    """---------------------------------------------------------------------------------------"""

                    """ E X I T """
                                           
                except KeyboardInterrupt:
                    MODEL_RUN  = 0
                    print 'Stop - Exception - Keyboard Interrupt'
                    pass

                # except Exception, err:
                #     MODEL_RUN  = 0
                #     print 'Stop - Exception - Error'
                #     print err
                #     pass
                
        
        if PLOT:
            PLOT        = 0         #Visualisations 
            vis.join()

        if HTM:
            for i in range(NOBINS):
                nupicObject[i].HTM = 0
            [nupicObject[i].join() for i in range(NOBINS)]                

        if AUDIO:
            audioObject.inStream.stop_stream()  #PyAudio
            audioObject.inStream.close()        #PyAudio 

        if FILES:
            for i in range(len(wavFiles)):
                wavFiles[i].FILES = 0
            [wavFiles[i].close() for i in range(len(wavFiles))]
            [wavFiles[i].join()  for i in range(len(wavFiles))]

        if DMX:
            dmx.DMX               = 0          #Serial
            dmx.join()                         #Serial
                                                                      
        print("Exit PyAudio, Matplotlib & Serial")
        sys.exit()                                                                                  
    


"""
Entrance to program
"""
GUI = interface()

