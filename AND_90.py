#!/usr/bin/env python
#-----------------------------------------------------------------------
# Name:         nupicAudioDMX
# Purpose:      Custom comisioned code - See README.md for details.
# Author:       IO - Code
# Created:      23/11/2015
# Copyright:    (c) IO - Code 2015
# License:      see License.txt
#-----------------------------------------------------------------------

import numpy                                # The language of pyaudio (& everything else)
import random                               # Use random numbers in some situations 
import time                                 # To keep track of processes´ times
import sys                                  # Systems functions, such as exit. 
import optparse                             # Used to Parse arguments, verbosity only implemented 
import threading                            # The whole project is build with threading. 
import ttk                                  # GUI
import glob                                 # The glob module finds all the pathnames matching a specified pattern
from Tkinter import *                       # GUI

import ModelParams                          # Parameters to build the NuPIC models
from Controls       import *                # General application parameters and logic
from NupicModels    import NupicModels      # NuPIC models thread
from Visualizations import Visualizations   # Plots thread
from AudioStream    import AudioStream      # Audio input thread
from AudioFile      import AudioFile        # Audio Files thread
from PyDMX          import PyDMX            # Serial, DMX thread

def destroy(e): sys.exit() # exit from the GUI

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
########################################################################################################

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
            ModelParams.MODEL_PARAMS['modelParams']['spParams']['columnCount']    = int(entryCOLUMNS.get())
            ModelParams.MODEL_PARAMS['modelParams']['tpParams']['columnCount']    = int(entryCOLUMNS.get())
            ModelParams.MODEL_PARAMS['modelParams']['tpParams']['cellsPerColumn'] = int(  entryCELLS.get())            

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
            audioObject = AudioStream(SR, BUFFERSIZE, BITRES, verbose)               
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
            wavFiles = [AudioFile(WAV_FILES[i], verbose) for i in range(len(WAV_FILES))]
            [wavFiles[i].start() for i in range(len(wavFiles))]
            print 'Loading following audio files: '
            print WAV_FILES
        

        """ Create DMX object, start thread outputs messages from a buffer"""  
        if DMX:
            print 'Start DMX Stream'      
            dmx = PyDMX(DMX_NUMBER, NOBINS, DMX_OFFSET, DMX_GAP, RGB, SERIAL_PORT, verbose)
            dmx.start()
            

        """ Start the NuPIC model """
        if HTM:
            nupicObject = [NupicModels(i,HTMHERTZ, verbose) for i in range(NOBINS)]
            [nupicObject[i].start() for i in range(NOBINS)]                        
            print 'Start NuPIC models'
            print "Number of NuPIC models:\t"+ str(NOBINS) 
        anomaly      = [i for i in range(NOBINS)]
        likelihood   = anomaly
        anomalyAv    = 0.5
        likelihoodAv = 0.5 #Range expanded and clipped for DMX Lighting reasons!


        """ Initialise the plots, BUFFERSIZE is the width of the plot. """
        if PLOT:            
            vis = Visualizations(BUFFERSIZE,FREQPERBIN, NOBINS, INDEXES, verbose)
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
                                if verbose:
                                    print 'Amplitude Model ' + str(i) + " set to: " + str(int(audioFFT[INDEXES[i]]))
                                nupicObject[i].amplitude    = int(audioFFT[INDEXES[i]])
                            elif audioFFT[INDEXES[i]] < GATE: #GATE!
                                if verbose:
                                    print 'Amplitude Model ' + str(i) + " set to: " + str(0)
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
    

if __name__ == "__main__":

    (options, args) = parser.parse_args()
    verbose = options.verbose
    print"Running... Press Ctrl+Z to force close"
    """
    Entrance to program
    """
    GUI = interface()



