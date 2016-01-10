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
import tkMessageBox                         # Message box for error messages for entry types. 

import ModelParams                          # Parameters to build the NuPIC models
from Controls       import *                # General application parameters and logic
from NupicModels    import NupicModels      # NuPIC models thread
from AudioStreamFFT import AudioStream      # Audio input thread
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

    def EntriesUpdate(self,*args):
        global SR
        try:
            SR      = int(self.entrySR.get())
        except :
            tkMessageBox.showinfo("Error", "Sample Rate must be a number.")
            error   = True  

    def AudioUpdate(self, *args):
        global AUDIO
        AUDIO  = self.audioVar.get()

    def HTMUpdate(self, *args):
        global HTM
        HTM    = self.htmVar.get()

    def DMXUpdate(self, *args):
        global DMX
        DMX    = self.dmxVar.get()

    def FilesUpdate(self, *args):
        global FILES
        FILES  = self.filesVar.get()

    def PlotUpdate(self, *args):
        global PLOT
        PLOT   = self.plotVar.get()

    def plot1Update(self, *args):
        global PLOT_1
        PLOT_1 = self.plot1Var.get()

    def plot2Update(self, *args):
        global PLOT_2
        PLOT_2 = self.plot2Var.get()

    def plot3Update(self, *args):
        global PLOT_3
        PLOT_3 = self.plot3Var.get()

    def plot4Update(self, *args):
        global PLOT_4
        PLOT_4 = self.plot4Var.get()
        

    def ControlUpdate(self, *args):
        global GATE
        global BRIGHTNESS
        global WAV_MINUTES
        global HTMHERTZ
        global INDEXES

        try: 
            GATE = int(self.entryGATE.get())          
        except ValueError:
            tkMessageBox.showinfo("Error","Gate Value must be a number")   
        
        try:
            BRIGHTNESS = float(self.entryDMXBRIGHT.get())
        except ValueError:
            tkMessageBox.showinfo("Error","Brightness Value must be a number")   

        try: 
            WAV_MINUTES = float(self.entryWAVMINS.get())
        except ValueError:
            tkMessageBox.showinfo("Error","Minutes of Interval in between WAV Files must be a number")
            
        try:
            HTMHERTZ    = int(self.entryHTMHERTZ.get())
        except ValueError:
            tkMessageBox.showinfo("Error","Frequency of Models computation must be a number")
            
        try:
            for i in range(len(self.entryFREQS)):
                INDEXES[i] = int(int(self.entryFREQS[i].get())/FREQPERBIN ) 
        except ValueError:
            tkMessageBox.showinfo("Error","Frequency values must be a number")

        try:
            for i in range(len(self.entryRGB)):
                RGB[i] = int(self.entryRGB[i].get())  
        except ValueError:
            tkMessageBox.showinfo("Error","Colour values must be a number")
                    

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

        error = False 

        AUDIO       = self.audioVar.get()
        FILES       = self.filesVar.get()
        HTM         = self.htmVar.get()
        DMX         = self.dmxVar.get()
        SERIAL_PORT = self.serialVar.get()

        PLOT        = self.plotVar.get()
        PLOT_1      = self.plot1Var.get()
        PLOT_2      = self.plot2Var.get()
        PLOT_3      = self.plot3Var.get()
        PLOT_4      = self.plot4Var.get()

        try:
            SR          = int(self.entrySR.get())
            self.entrySR.config(state=DISABLED)
        except :
            tkMessageBox.showinfo("Error", "Sample Rate must be a number.")
            error   = True        

        try:
            noFiles     = int(self.entryFILESNUM.get())
            self.entryFILESNUM.config(state=DISABLED)
        except ValueError:
            tkMessageBox.showinfo("Error","Number of Files must be a number")
            error = True

        WAV_FILES       = [(str(i+1)+'.wav') for i in range(noFiles)]

        try: 
            WAV_MINUTES = float(self.entryWAVMINS.get())
        except ValueError:
            tkMessageBox.showinfo("Error","Minutes Interval in between WAV Files must be a number")
            error = True        

        try:
            NOBINS      = int(self.entryMODELNUM.get())
            self.entryMODELNUM.config(state=DISABLED)
        except ValueError:
            tkMessageBox.showinfo("Error","Number of Models must be a number")
            error = True

        try:
            HTMHERTZ    = int(self.entryHTMHERTZ.get())
        except ValueError:
            tkMessageBox.showinfo("Error","Frequency of Models computation must be a number")
            error = True

        try:
            ModelParams.MODEL_PARAMS['modelParams']['spParams']['columnCount']    = int(self.entryCOLUMNS.get())
            ModelParams.MODEL_PARAMS['modelParams']['tpParams']['columnCount']    = int(self.entryCOLUMNS.get())
            self.entryCOLUMNS.config(state=DISABLED)
        except ValueError:
            tkMessageBox.showinfo("Error","Quantity of Columns must be a number")
            error = True

        try:
            ModelParams.MODEL_PARAMS['modelParams']['tpParams']['cellsPerColumn'] = int(  self.entryCELLS.get()) 
            self.entryCELLS.config(state=DISABLED)
        except ValueError:
            tkMessageBox.showinfo("Error","Quantity of Cells must be a number")
            error = True          

        try:
            DMX_NUMBER  = int(self.entryDMXNUM.get()) 
            self.entryDMXNUM.config(state=DISABLED)
        except ValueError:
            tkMessageBox.showinfo("Error","Number of DMX Fixtures must be a number")
            error = True 

        try:
            DMX_GAP     = int(self.entryDMXGAP.get())
            self.entryDMXGAP.config(state=DISABLED)
        except ValueError:
            tkMessageBox.showinfo("Error","Channel Gap in between DMX Fixtures must be a number")
            error = True 

        try:
            DMX_OFFSET  = int(self.entryDMXOFFST.get())
            self.entryDMXOFFST.config(state=DISABLED)
        except ValueError:
            tkMessageBox.showinfo("Error","DMX Offset must be a number")
            error = True 

        try:
            BRIGHTNESS  = float(self.entryDMXBRIGHT.get()) 
        except ValueError:
            tkMessageBox.showinfo("Error","DMX Brightness must be a number")
            error = True 

        try:
            for i in range(len(self.entryFREQS)):
                INDEXES[i] = int(int(self.entryFREQS[i].get())/FREQPERBIN ) 
        except ValueError:
            tkMessageBox.showinfo("Error","Frequency values must be a number")
            error = True 
                     
        try:
            for i in range(len(self.entryRGB)):
                RGB[i] = int(self.entryRGB[i].get()) 
        except ValueError:
            tkMessageBox.showinfo("Error","Colour values must be a number")
            error = True 
                  

        if not error:
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
        self.nupicAudioDMX = Main() #4 bins 
        self.nupicAudioDMX.start()
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
        self.dmxVar.set  (1)
        self.audioVar.set(1)
        self.filesVar.set(0)
        self.plotVar.set (1)
        self.htmVar.set  (1)
        self.plot1Var.set(1)
        self.plot2Var.set(1)
        self.plot3Var.set(1)
        self.plot4Var.set(1)
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

        self.entryGATE.place(     x=leftMargin+0.5*width,                     y=(5*rowHeight)+(4*space), width=width/4,   height=rowHeight) 
        self.entrySR.place(       x=leftMargin+width/2,                       y=(3*rowHeight)+(2*space), width=width/2,   height=rowHeight)
        self.entryFILESNUM.place( x=leftMargin+width*2/3,                     y=(8*rowHeight)+(7*space), width=width/3,   height=rowHeight)
        self.entryWAVMINS.place(  x=leftMargin+width*2/3,                     y=(9*rowHeight)+(8*space), width=width/3,   height=rowHeight)  
        self.entryMODELNUM.place( x=leftMargin+(2*width)+width,               y=(3*rowHeight)+(2*space), width=width/2,   height=rowHeight)  
        self.entryCOLUMNS.place(  x=leftMargin+(2*width)+width,               y=(4*rowHeight)+(3*space), width=width/2,   height=rowHeight)  
        self.entryCELLS.place(    x=leftMargin+(2*width)+width,               y=(5*rowHeight)+(4*space), width=width/2,   height=rowHeight)
        self.entryHTMHERTZ.place( x=leftMargin+(2*width)+width,               y=(6*rowHeight)+(5*space), width=width/2,   height=rowHeight)  
        self.entryDMXNUM.place(   x=leftMargin+(4.5*width),                   y=(3*rowHeight)+(2*space), width=width/4,   height=rowHeight)
        self.entryDMXGAP.place(   x=leftMargin+(4.66*width),                  y=(7*rowHeight)+(6*space), width=width/3,   height=rowHeight) 
        self.entryDMXOFFST.place( x=leftMargin+(5*width),                     y=(8*rowHeight)+(7*space), width=width/3,   height=rowHeight)
        self.entryDMXBRIGHT.place(x=leftMargin+(5*width),                     y=(9*rowHeight)+(8*space), width=width/3,   height=rowHeight)   
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

        self.entryFREQS[0].insert(END, INDEXES[0]*FREQPERBIN)        
        self.entryFREQS[1].insert(END, INDEXES[1]*FREQPERBIN)   
        self.entryFREQS[2].insert(END, INDEXES[2]*FREQPERBIN)            
        self.entryFREQS[3].insert(END, INDEXES[3]*FREQPERBIN)

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
        ttk.Label(root, text="Gate"    ).place(x=leftMargin,                   y=(5*rowHeight)+(4*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="dB"      ).place(x=leftMargin+0.75*width,        y=(5*rowHeight)+(4*space), width=width/4,     height=rowHeight)
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
        ttk.Label(root, text="Plot"    ).place(x=2*leftMargin+(6*width),       y=rowHeight ,              width=500,         height=rowHeight)
        ttk.Label(root, text="Audio"   ).place(x=2*leftMargin+(6*width),       y=(4*rowHeight)+(3*space), width=50,          height=rowHeight)
        ttk.Label(root, text="FFT"     ).place(x=2*leftMargin+(6*width),       y=(6*rowHeight)+(5*space), width=50,          height=rowHeight)
        ttk.Label(root, text="Anly"    ).place(x=2*leftMargin+(6*width),       y=(8*rowHeight)+(7*space), width=50,          height=rowHeight)
        ttk.Label(root, text="Lklhd"   ).place(x=2*leftMargin+(6*width),       y=(10*rowHeight)+(9*space),width=50,          height=rowHeight)
        ttk.Label(root, text="DMX"     ).place(x=leftMargin+(4*width),         y=(2*rowHeight)+(1*space), width=width-space, height=rowHeight)
        ttk.Label(root, text="Chls."   ).place(x=leftMargin+(4*width),         y=(3*rowHeight)+(2*space), width=width/2,     height=rowHeight)
        ttk.Label(root, text="DMX Gap" ).place(     x=leftMargin+(4*width),    y=(7*rowHeight)+(6*space), width=2*width/3,   height=rowHeight)
        ttk.Label(root, text="First Channel").place(x=leftMargin+(4*width),    y=(8*rowHeight)+(7*space), width=width-3,     height=rowHeight)
        ttk.Label(root, text='Brightness').place(   x=leftMargin+(4*width),    y=(9*rowHeight)+(8*space), width=width-3,     height=rowHeight)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Button Objects and their position  """                                                                         
        ttk.Button(root, text="Start", command=self.startProgram ).place(x=leftMargin+4*width,           y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text="Pause", command=self.pauseProgram ).place(x=leftMargin+4*width+2*width/3, y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text="Stop",  command=self.stopProgram  ).place(x=leftMargin+4*width+4*width/3, y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        ttk.Button(root, text='Updt',command=self.ControlUpdate).place(x=leftMargin+3*width+width/3,   y=(10*rowHeight)+(9*space), width=2*width/3-5, height=rowHeight)
        """-----------------------------------------------------------------------------------------------------------------------------"""


        """ Checkbutton Objects and their position """
        ttk.Checkbutton(root, variable=self.dmxVar,  command=self.DMXUpdate  ).place(x=leftMargin+(4.75*width),              y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.audioVar,command=self.AudioUpdate).place(x=leftMargin+(0.75*width) ,             y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.filesVar,command=self.FilesUpdate).place(x=leftMargin+(0.75*width) ,             y=(7*rowHeight)+(6*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.htmVar,  command=self.HTMUpdate  ).place(x=leftMargin+(2*1*width)+1.25*width ,   y=(2*rowHeight)+(1*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.plotVar, command=self.PlotUpdate ).place(x=3*leftMargin+(6*width)+450 ,          y=rowHeight              , width=rowHeight, height=rowHeight)

        ttk.Checkbutton(root, variable=self.plot1Var,command=self.plot1Update).place(x=2*leftMargin+(6*width) ,   y=(3*rowHeight)+(2*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.plot2Var,command=self.plot2Update).place(x=2*leftMargin+(6*width) ,   y=(5*rowHeight)+(4*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.plot3Var,command=self.plot3Update).place(x=2*leftMargin+(6*width) ,   y=(7*rowHeight)+(6*space), width=rowHeight, height=rowHeight)
        ttk.Checkbutton(root, variable=self.plot4Var,command=self.plot4Update).place(x=2*leftMargin+(6*width) ,   y=(9*rowHeight)+(8*space), width=rowHeight, height=rowHeight)

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
        plot = Plot(root, PLOT_WIDTH, NOBINS, 1, 1, 1, 1, verbose)

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
        likelihoodAv = 0.5 #Range expanded and clipped for DMX Lighting !
        

        """ Create DMX object, start thread outputs messages from a buffer"""  
        if DMX:
            print 'Start DMX Stream'      
            dmx = PyDMX(DMX_NUMBER, NOBINS, DMX_OFFSET, DMX_GAP, RGB, SERIAL_PORT, verbose)
            dmx.start()


        """ Initialise the plots, BUFFERSIZE is the width of the plot. """
        if PLOT:
            plot.start()
            plot.size = NOBINS
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
                            wavFiles[int(anomalyAv*(len(wavFiles)-1))].play = 1
                            elapsed = time.time()
                            if verbose:
                                print 'Audio for Anomaly: ' + str(anomalyAv) 
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
                        #dmx.CYCLE += 1###############################
                        if(dmx.CYCLE > 255):
                            dmx.CYCLE = 0

                    if DMX and HTM == 0:
                        if 1 < audioFFT[10] and  audioFFT[10] < 255:
                            #dmx.VALUES = int(audioObject.ys[10])# Send the audio value as DMX
                            dmx.VALUES = random.randint(0,1)
                        else:
                            dmx.VALUES = 0  ########## REVISE THIS AS THIS CYCLE VARIABLE MIGHT BE UNUSED
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

                except Exception, err:
                    MODEL_RUN  = 0
                    print 'Stop - Exception - Error'
                    print err
                    pass
                
        
        if PLOT:
            plot.PLOT        = 0                # Visualisations 
            plot.join()                         # Join to main thread

        if HTM:
            for i in range(NOBINS):
                nupicObject[i].HTM = 0          # HTM Models
            [nupicObject[i].join() for i in range(NOBINS)]                

        if AUDIO:
            audioObject.inStream.stop_stream()  # PyAudio
            audioObject.inStream.close()        # Join to main thread 

        if FILES:
            for i in range(len(wavFiles)):
                wavFiles[i].FILES = 0           # WAV Files
            [wavFiles[i].close() for i in range(len(wavFiles))]
            [wavFiles[i].join()  for i in range(len(wavFiles))]

        if DMX:
            dmx.DMX               = 0           # Serial
            dmx.join()                          # Join to main thread
                                                                      
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



