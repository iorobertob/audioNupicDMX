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
import time                                 # To keep track of processes' times
import sys                                  # Systems functions, such as exit. 
import optparse                             # Used to Parse arguments, verbosity only implemented 
import threading                            # The whole project is build with threading. 
import ttk                                  # GUI
import glob                                 # The glob module finds all the pathnames matching a specified pattern
from Tkinter import *                       # GUI

import ModelParams                          # Parameters to build the NuPIC models
from Controls       import *                # General application parameters and logic
from NupicModels    import NupicModels      # NuPIC models thread
#from Visualizations import Visualizations   # Plots thread
from AudioStream    import AudioStream      # Audio input thread
from AudioFile      import AudioFile        # Audio Files thread
from PyDMX          import PyDMX            # Serial, DMX thread

from Plot           import Plot

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


    def gateControl(self, *args):
        global GATE 
        GATE = int(self.entryGATE.get())
        print "Noise Gate set to " + str(self.entryGATE.get()) + " dB"

    def setBright(self, *args):
        global BRIGHTNESS
        BRIGHTNESS = float(self.entryDMXBRIGHT.get())
        print "Brightness: " + str(BRIGHTNESS)

    def on_closing(self, *args):
        global MODEL_RUN
        global PAUSE
        global root
        print 'Stop'
        PAUSE       = 0
        MODEL_RUN   = 0
        root.destroy()
        sys.exit()

    def stopProgram(self, *args):
        global MODEL_RUN
        global PAUSE
        print 'Stop '
        PAUSE       = 0
        MODEL_RUN   = 0

    def pauseProgram(self, *args):
        print'Pause'
        global PAUSE
        PAUSE       = 0

    def startProgram(self, *args):
        global model_params
                  
        global PLOT
        global PLOT_1
        global PLOT_2
        global PLOT_3
        global PLOT_4

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

        AUDIO       =             self.audioVar.get()
        SR          =          int(self.entrySR.get())
        FILES       =             self.filesVar.get()
        noFiles     =    int(self.entryFILESNUM.get())
        WAV_FILES   = [(str(i+1)+'.wav') for i in range(noFiles)] 
        WAV_MINUTES =   float(self.entryWAVMINS.get())           

        HTM         =               self.htmVar.get()
        NOBINS      =    int(self.entryMODELNUM.get())
        HTMHERTZ    =    int(self.entryHTMHERTZ.get())
        ModelParams.MODEL_PARAMS['modelParams']['spParams']['columnCount']    = int(self.entryCOLUMNS.get())
        ModelParams.MODEL_PARAMS['modelParams']['tpParams']['columnCount']    = int(self.entryCOLUMNS.get())
        ModelParams.MODEL_PARAMS['modelParams']['tpParams']['cellsPerColumn'] = int(  self.entryCELLS.get())            

        DMX         =               self.dmxVar.get()
        SERIAL_PORT =            self.serialVar.get()
        DMX_NUMBER  =      int(self.entryDMXNUM.get())
        DMX_GAP     =      int(self.entryDMXGAP.get())
        DMX_OFFSET  =    int(self.entryDMXOFFST.get())
        BRIGHTNESS  = float(self.entryDMXBRIGHT.get()) 

        PLOT        =              self.plotVar.get()
        PLOT_1      = self.plot1Var.get()
        PLOT_2      = self.plot2Var.get()
        PLOT_3      = self.plot3Var.get()
        PLOT_4      = self.plot4Var.get()
        
        for i in range(len(self.entryFREQS)):
            INDEXES[i] = int(int(self.entryFREQS[i].get())/FREQPERBIN )               

        for i in range(len(self.entryRGB)):
            RGB[i] = int(self.entryRGB[i].get())                

        START   = 1
        PAUSE   = 1
        print 'Start'
        print 'Frequencies to Analyse:'
        print self.entryFREQS[0].get() + " Hz, " + self.entryFREQS[1].get() + " Hz, " + self.entryFREQS[2].get() + " Hz, and " + self.entryFREQS[3].get() + " Hz."




    def __init__(self):
            
            
        """-----------------------------------------------------------------------------------------------------------------------------"""
                            
        """ Start building the interface - Variables """              
        winX        = 700
        winY        = 350
        rowHeight   = 25
        columns     = 3        
        space       = 10
        leftMargin  = 25
        width       = (winX-(2*leftMargin))/(2*columns)

        global root 
        root = Tk()
        root.title("Audio NuPIC DMX")
        root.geometry("700x400")
        """-----------------------------------------------------------------------------------------------------------------------------"""

        """ Create Main Object """
        nupicAudioDMX = Main() #4 bins 
        nupicAudioDMX.start()
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Variables for Checkboxes  """
        self.dmxVar      = IntVar()
        self.audioVar    = IntVar()
        self.filesVar    = IntVar()
        self.plotVar     = IntVar()
        self.htmVar      = IntVar()
        self.plot1Var    = IntVar()
        self.plot2Var    = IntVar()
        self.plot3Var    = IntVar()
        self.plot4Var    = IntVar()
        self.dmxVar.set  (0)
        self.audioVar.set(1)
        self.filesVar.set(0)
        self.plotVar.set (1)
        self.htmVar.set  (1)
        self.plot1Var.set(0)
        self.plot2Var.set(0)
        self.plot3Var.set(0)
        self.plot4Var.set(0)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Entry Objects and their Position"""

        self.entryFREQS = [Entry(root) for i in range(FREQS)] 
        self.entryRGB   = [Entry(root) for i in range(3*DMX_NUMBER)]     

        self.entryGATE       = Entry(root)
        self.entrySR         = Entry(root)
        self.entryFILESNUM   = Entry(root)
        self.entryWAVMINS    = Entry(root)
        self.entryFREQNUM    = Entry(root) 
        self.entryMODELNUM   = Entry(root) 
        self.entryCOLUMNS    = Entry(root) 
        self.entryCELLS      = Entry(root)
        self.entryHTMHERTZ   = Entry(root)
        self.entryDMXNUM     = Entry(root)
        self.entryDMXGAP     = Entry(root) 
        self.entryDMXOFFST   = Entry(root)  
        self.entryDMXBRIGHT  = Entry(root)      
        
        self.entryFREQS[0].place( x=leftMargin+1.5*width,                     y=(2*rowHeight)+(1*space), width=width/2,   height=rowHeight)
        self.entryFREQS[1].place( x=leftMargin+1.5*width,                     y=(3*rowHeight)+(2*space), width=width/2,   height=rowHeight)
        self.entryFREQS[2].place( x=leftMargin+1.5*width,                     y=(4*rowHeight)+(3*space), width=width/2,   height=rowHeight)
        self.entryFREQS[3].place( x=leftMargin+1.5*width,                     y=(5*rowHeight)+(4*space), width=width/2,   height=rowHeight)

        self.entryGATE.place(     x=leftMargin,                               y=(5*rowHeight)+(4*space), width=width/4,   height=rowHeight) 
        self.entrySR.place(       x=leftMargin+width/2,                       y=(3*rowHeight)+(2*space), width=width/2,   height=rowHeight)
        self.entryFILESNUM.place( x=leftMargin+width*2/3,                     y=(8*rowHeight)+(7*space), width=width/3,   height=rowHeight)
        self.entryWAVMINS.place(  x=leftMargin+width*2/3,                     y=(9*rowHeight)+(8*space), width=width/3,   height=rowHeight)  
        self.entryMODELNUM.place( x=leftMargin+(2*width)+width,               y=(3*rowHeight)+(2*space), width=width/2,   height=rowHeight)  
        self.entryCOLUMNS.place(  x=leftMargin+(2*width)+width,               y=(4*rowHeight)+(3*space), width=width/2,   height=rowHeight)  
        self.entryCELLS.place(    x=leftMargin+(2*width)+width,               y=(5*rowHeight)+(4*space), width=width/2,   height=rowHeight)
        self.entryHTMHERTZ.place( x=leftMargin+(2*width)+width,               y=(6*rowHeight)+(5*space), width=width/2,   height=rowHeight)  
        self.entryDMXNUM.place(   x=leftMargin+(4.5*width),                   y=(3*rowHeight)+(2*space), width=width/4,   height=rowHeight)
        self.entryDMXGAP.place(   x=leftMargin+(4.66*width),                  y=(7*rowHeight)+(6*space), width=width/3,   height=rowHeight) 
        self.entryDMXOFFST.place( x=leftMargin+(5*width),                     y=(8*rowHeight)+(7*space), width=width/2,   height=rowHeight)
        self.entryDMXBRIGHT.place(x=leftMargin+(5*width),                     y=(9*rowHeight)+(8*space), width=width/2,   height=rowHeight)   
        self.entryRGB[0].place(   x=leftMargin+(4*width)+0*(width/3-3)      , y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight)
        self.entryRGB[1].place(   x=leftMargin+(4*width)+1*(width/3-3)      , y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight)
        self.entryRGB[2].place(   x=leftMargin+(4*width)+2*(width/3-3)      , y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight)
        self.entryRGB[3].place(   x=leftMargin+(4*width)+0*(width/3-3)      , y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight)
        self.entryRGB[4].place(   x=leftMargin+(4*width)+1*(width/3-3)      , y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight)
        self.entryRGB[5].place(   x=leftMargin+(4*width)+2*(width/3-3)      , y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight)
        self.entryRGB[6].place(   x=leftMargin+(4*width)+3*(width/3-3)+space, y=(2*rowHeight)+(1*space), width=width/3-3, height=rowHeight)               
        self.entryRGB[7].place(   x=leftMargin+(4*width)+4*(width/3-3)+space, y=(2*rowHeight)+(1*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[8].place(   x=leftMargin+(4*width)+5*(width/3-3)+space, y=(2*rowHeight)+(1*space), width=width/3-3, height=rowHeight)
        self.entryRGB[9].place(   x=leftMargin+(4*width)+3*(width/3-3)+space, y=(3*rowHeight)+(2*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[10].place(  x=leftMargin+(4*width)+4*(width/3-3)+space, y=(3*rowHeight)+(2*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[11].place(  x=leftMargin+(4*width)+5*(width/3-3)+space, y=(3*rowHeight)+(2*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[12].place(  x=leftMargin+(4*width)+3*(width/3-3)+space, y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[13].place(  x=leftMargin+(4*width)+4*(width/3-3)+space, y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[14].place(  x=leftMargin+(4*width)+5*(width/3-3)+space, y=(4*rowHeight)+(3*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[15].place(  x=leftMargin+(4*width)+3*(width/3-3)+space, y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[16].place(  x=leftMargin+(4*width)+4*(width/3-3)+space, y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight) 
        self.entryRGB[17].place(  x=leftMargin+(4*width)+5*(width/3-3)+space, y=(5*rowHeight)+(4*space), width=width/3-3, height=rowHeight) 

        self.entryFREQS[0].insert(END, INDEXES[0])        
        self.entryFREQS[1].insert(END, INDEXES[1])   
        self.entryFREQS[2].insert(END, INDEXES[2])            
        self.entryFREQS[3].insert(END, INDEXES[3])

        self.entryGATE.insert(    END, 40)   
        self.entrySR.insert(      END, SR)
        self.entryFILESNUM.insert(END, 2) 
        self.entryWAVMINS.insert( END, 5)       
        self.entryMODELNUM.insert(END, 4)      
        self.entryCOLUMNS.insert( END, 2048)  
        self.entryCELLS.insert(   END, 32)
        self.entryHTMHERTZ.insert(END, HTMHERTZ)     
        self.entryDMXNUM.insert(  END, DMX_NUMBER)
        self.entryDMXGAP.insert(  END, DMX_GAP)
        self.entryDMXOFFST.insert(END, DMX_OFFSET)
        self.entryDMXBRIGHT.insert(END,BRIGHTENESS) 

        self.entryRGB[0].insert(END, 255)        
        self.entryRGB[1].insert(END, 80) # RED        
        self.entryRGB[2].insert(END, 80)

        self.entryRGB[3].insert(END, 255)   
        self.entryRGB[4].insert(END, 255)# YELLOW   
        self.entryRGB[5].insert(END, 0)

        self.entryRGB[6].insert(END, 255)   
        self.entryRGB[7].insert(END, 153) # ORANGE  
        self.entryRGB[8].insert(END, 51)

        self.entryRGB[9].insert(END, 51)   
        self.entryRGB[10].insert(END, 204) # GREEN  
        self.entryRGB[11].insert(END, 51)

        self.entryRGB[12].insert(END, 51)   
        self.entryRGB[13].insert(END, 102) # BLUE  
        self.entryRGB[14].insert(END, 255)

        self.entryRGB[15].insert(END, 204)   
        self.entryRGB[16].insert(END, 0)   # PURPLE
        self.entryRGB[17].insert(END, 255) 
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
        ttk.Label(root, text="mins."    ).place(x=leftMargin+width,            y=(9*rowHeight)+(8*space), width=width/3,     height=rowHeight)
        ttk.Label(root, text="HTM"     ).place(x=leftMargin+(2*width)+width/2, y=(2*rowHeight)+(1*space), width=width,       height=rowHeight)
        ttk.Label(root, text="Models"  ).place(x=leftMargin+(2*width)+width/2, y=(3*rowHeight)+(2*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Cols."   ).place(x=leftMargin+(2*width)+width/2, y=(4*rowHeight)+(3*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Cells"   ).place(x=leftMargin+(2*width)+width/2, y=(5*rowHeight)+(4*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Hertz"   ).place(x=leftMargin+(2*width)+width/2, y=(6*rowHeight)+(5*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="Plot"    ).place(x=leftMargin+(2*width)+width/2, y=(7*rowHeight)+(6*space), width=width,       height=rowHeight)
        ttk.Label(root, text="DMX"     ).place(x=leftMargin+(4*width),         y=(2*rowHeight)+(1*space), width=width-space, height=rowHeight)
        ttk.Label(root, text="Chls."   ).place(x=leftMargin+(4*width),         y=(3*rowHeight)+(2*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="DMX Gap" ).place(     x=leftMargin+(4*width),    y=(7*rowHeight)+(6*space), width=2*width/3,   height=rowHeight)
        ttk.Label(root, text="First Channel").place(x=leftMargin+(4*width),    y=(8*rowHeight)+(7*space), width=width-3,     height=rowHeight)
        ttk.Label(root, text='Brightness').place(   x=leftMargin+(4*width),    y=(9*rowHeight)+(8*space), width=width-3,     height=rowHeight)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Button Objects and their position  """

        ttk.Button(root, text="Start", command=self.startProgram).place(x=leftMargin+4*width,           y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text="Pause", command=self.pauseProgram).place(x=leftMargin+4*width+2*width/3, y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text="Stop",  command=self.stopProgram ).place(x=leftMargin+4*width+4*width/3, y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text='Set',   command=self.setBright   ).place(x=leftMargin+(5.5*width),       y=(9*rowHeight)+(8*space),  width=width/2-5,   height=rowHeight)
        ttk.Button(root, text="Gate",  command =self.gateControl).place(x=leftMargin+(width/2),         y=(5*rowHeight)+(4*space),  width=width/2,     height=rowHeight)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Checkbutton Objects and their position """

        ttk.Checkbutton(root, variable=self.dmxVar  ).place(x=leftMargin+(4.75*width),              y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.audioVar).place(x=leftMargin+(0.75*width) ,             y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.filesVar).place(x=leftMargin+(0.75*width) ,             y=(7*rowHeight)+(6*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.htmVar  ).place(x=leftMargin+(2*1*width)+1.25*width ,   y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.plotVar ).place(x=leftMargin+(2*1*width)+1.25*width ,   y=(7*rowHeight)+(6*space), width=rowHeight, height=rowHeight)

        ttk.Checkbutton(root, variable=self.plot1Var ).place(x=leftMargin+(2*3*width)+1.75 ,   y=(1.40*rowHeight)+(5*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.plot2Var ).place(x=leftMargin+(2*3*width)+1.75 ,   y=(4*rowHeight)+(5*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.plot3Var ).place(x=leftMargin+(2*3*width)+1.75 ,   y=(6.6*rowHeight)+(5*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.plot4Var ).place(x=leftMargin+(2*3*width)+1.75 ,   y=(9.2*rowHeight)+(5*space), width=rowHeight, height=rowHeight)

        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ OptionMenu Object """

        ports = glob.glob('/dev/tty.*')         
        self.serialVar = StringVar()
        omSERIALPORT = ttk.OptionMenu(root, self.serialVar, ports[0], *ports)
        omSERIALPORT.place(x=leftMargin+(2*2*width), y=(6*rowHeight)+(5*space),width=2*width, height=rowHeight     )
        """-----------------------------------------------------------------------------------------------------------------------------"""

        """ Start the GUI """

        root.bind('<Return>', self.startProgram)
        root.protocol("WM_DELETE_WINDOW",self.on_closing)
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
        global BRIGHTNESS
        global CYCLE
        global PLOT
        global PLOT_1
        global PLOT_2
        global PLOT_3
        global PLOT_4
        global START        
        global MODEL_RUN
        global PAUSE 

        global root       
        
        print 'Start MatPlotLib' 
        plot = Plot(root, 200, NOBINS, 1, 1, 1, 1)

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
        

        """ Create DMX object, start thread outputs messages from a buffer"""  
        if DMX:
            print 'Start DMX Stream'      
            dmx = PyDMX(DMX_NUMBER, NOBINS, DMX_OFFSET, DMX_GAP, RGB, SERIAL_PORT, verbose)
            dmx.start()


        """ Initialise the plots, BUFFERSIZE is the width of the plot. """
        if PLOT:
            #print 'Start MatPlotLib' 
            #plot = Plot(root, 200, NOBINS, 1, 1, 1, 1)
            if PLOT_1:
                plot.PLOT_A = 1

            if PLOT_2:
                plot.PLOT_B = 1 
            
            if PLOT_3:
                plot.PLOT_C = 1

            if PLOT_4:
                plot.PLOT_D = 1     
            """-----------------------------------------------------------------------------------------------------------------------------"""          
            

        """
        Start the Main Thread Loop.
        """
        MODEL_RUN   = 1
        startTime   = time.time()
        elapsed     = startTime
        
        

        while MODEL_RUN:  

            while PAUSE:
                try:

                    """ AUDIO STREAM  - ...      """
                    if AUDIO:
                        audio       = audioObject.audio
                        audioFFT    = audioObject.audioFFT
                    """---------------------------------------------------------------------------------------"""
                    
                    """ WAV FILES - Play a number of wav files sorted corresponding to the anomaly value """

                    if FILES:
                        if time.time()-elapsed > WAV_MINUTES*60:                        
                            print 'Audio for Anomaly: ' + str(anomalyAv) 
                            wavFiles[int(anomalyAv*(len(wavFiles)-1))].play = 1

                            elapsed = time.time()
                    """---------------------------------------------------------------------------------------"""

                    """ NUPIC MODEL - Run the NuPIC model and get the anomaly score back. Feed on bin only."""
                                            
                    if HTM and AUDIO: 
                        for i in range(NOBINS):
                            if audioFFT[INDEXES[i]] >= GATE and audioFFT[INDEXES[i]] < 200:
                                nupicObject[i].amplitude    = int(audioFFT[INDEXES[i]])
                                if verbose:
                                    print 'Amplitude Model ' + str(i) + " set to: " + str(int(audioFFT[INDEXES[i]]))
                                
                            elif audioFFT[INDEXES[i]] < GATE: #GATE!
                                nupicObject[i].amplitude    = 0 
                                if verbose:
                                    print 'Amplitude Model ' + str(i) + " set to: " + str(0)
                                                       
                        anomaly      = [nupicObject[i].anomaly    for i in range(NOBINS)]
                        likelihood   = [nupicObject[i].likelihood for i in range(NOBINS)]
                        anomalyAv    = numpy.sum(anomaly)   /NOBINS
                        likelihoodAv = numpy.sum(likelihood)/NOBINS #Range expanded and clipped for DMX Lighting reasons!
                        if verbose:
                            print "Anomaly : " + str(anomaly)

                    if HTM and AUDIO == 0:
                        for i in range(NOBINS):
                            nupicObject[i].amplitude    = random.randint(0,200)
                            if verbose:
                                    print 'Amplitude Model ' + str(i) + " randomly set to: " + str(nupicObject[i].amplitude)
                                    
                        anomaly      = [nupicObject[i].anomaly    for i in range(NOBINS)]
                        likelihood   = [nupicObject[i].likelihood for i in range(NOBINS)]
                        anomalyAv    = numpy.sum(anomaly)   /NOBINS
                        likelihoodAv = numpy.sum(likelihood)/NOBINS #Range expanded and clipped for DMX Lighting reasons!
                        if verbose:
                            print "Anomaly No Audio : " + str(anomaly)
                    """---------------------------------------------------------------------------------------"""

                    """ DMX - Pass Likelihood value to the DMX Thread. Clip values below 0."""
                    if DMX and HTM:
                        dmx.BRIGHTNESS = BRIGHTNESS
                        if anomalyAv < 0:
                            dmx.VALUES = [0]*NOBINS                   
                        if anomalyAv > 0.17:
                            #dmx.VALUES = int(anomalyAv*255)#CHANGE OR ADD self.anomalyLikelihood
                            dmx.VALUES = anomaly                            
                            #dmx.VALUES = int(likelihoodAv*300 -50)#CHANGE OR ADD self.anomalyLikelihood
                        # Cycle the colour values of the DMX channels, keeping their RGB proportion, and cycling through 255 steps
                        dmx.CYCLE += 1
                        if(dmx.CYCLE > 255):
                            dmx.CYCLE = 0

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
                        if PLOT_1:   
                            plot.newAValues = audio[0]/2

                        if PLOT_2:
                            for i in range(NOBINS):
                                plot.newBValues[i] = audioFFT[INDEXES[i]]

                        if PLOT_3:
                            plot.newCValues = anomaly

                        if PLOT_4:
                            plot.newDValues = likelihood  
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
            plot.PLOT        = 0         #Visualisations 
            plot.join()

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



