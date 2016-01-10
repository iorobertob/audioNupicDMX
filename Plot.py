# The code for changing pages was derived from: http://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
# License: http://creativecommons.org/licenses/by-sa/3.0/	

import threading 
import time
import random
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure                 import Figure
from collections                       import deque


class Plot(threading.Thread):

        def __init__(self,root, Xaxis, size, A, B, C, D, verbose):

            threading.Thread.__init__(self)
            self.daemon = True
            self.Xaxis  = Xaxis
            self.size   = size
            self.verbose= verbose

            font = {
            'weight':100,
            'size'  :6
            }

            matplotlib.rc('font',**font)
            """-----------------------------------------------------------------------------------------------------------------------------"""

            """ Setting up the Figure """

            root.geometry("1225x425")
            self.f = Figure(figsize=(5,5), dpi=100)


            """-----------------------------------------------------------------------------------------------------------------------------"""

            """ Line vectors to plot, size+1 for plots A, C and D, and size=1 for B """
            self.plotALines = deque([0.0]*self.Xaxis)
            self.plotBLines = []
            self.plotCLines = []
            self.plotDLines = []
            for i in range(self.size+1):
                self.plotBLines.append (deque([0.0]*self.Xaxis))  # arrays of size (self.size+1) x self.Axis
                self.plotCLines.append (deque([0.0]*self.Xaxis))
                self.plotDLines.append (deque([0.0]*self.Xaxis))
            """-----------------------------------------------------------------------------------------------------------------------------"""

            """ Subplots to add to the figure """

            self.a = self.f.add_subplot(411)
            self.b = self.f.add_subplot(412)
            self.c = self.f.add_subplot(413)
            self.d = self.f.add_subplot(414)
            """-----------------------------------------------------------------------------------------------------------------------------"""

            """ New Values to be added at the end of the Line's vector """
            self.newAValues = 0.0
            self.newBValues = [0.0]*(size+1)
            self.newCValues = [0.0]*(size+1)
            self.newDValues = [0.0]*(size+1)
            """-----------------------------------------------------------------------------------------------------------------------------"""

            """ Actual plots, one per line, that is size+1 plots in the multiline subplots """
            self.aPlot, = self.a.plot(range(Xaxis), range(Xaxis))
            self.bPlot = []
            self.cPlot = []
            self.dPlot = []
            for i in range(self.size):
                tempPlot, = self.b.plot(range(Xaxis), [0]*(Xaxis))
                self.bPlot.append(tempPlot)

            for i in range(self.size):
                tempPlot, = self.c.plot(range(Xaxis), [0]*(Xaxis))
                self.cPlot.append(tempPlot)
                               
                tempPlot, = self.d.plot(range(Xaxis), [0]*(Xaxis))
                self.dPlot.append(tempPlot)
            """-----------------------------------------------------------------------------------------------------------------------------"""

            """ Final settings and display """
            self.a.set_ylim(-1000,1000)
            self.b.set_ylim(50,  100)            
            self.c.set_ylim(0.0  ,1.0)
            self.d.set_ylim(0.0  ,1.0)
            
            self.canvas = FigureCanvasTkAgg(self.f, root)
            self.canvas.show()
            self.canvas.get_tk_widget().place(x=750,y=50, width=450, height=350)
            
            self.PLOT   = 1
            self.PLOT_A = A
            self.PLOT_B = B
            self.PLOT_C = C
            self.PLOT_D = D

            """-----------------------------------------------------------------------------------------------------------------------------"""


        def run(self):
            startTime   = time.time()
            while self.PLOT:

                if self.PLOT_A:
                    self.plotALines.rotate(-1)
                    self.plotALines[self.Xaxis-1] = self.newAValues
                    self.aPlot.set_ydata(self.plotALines)

                if self.PLOT_B:
                    for i in range(self.size):
                        self.plotBLines[i].rotate(-1)
                        self.plotBLines[i][self.Xaxis-1] = self.newBValues[i] 
                        self.bPlot[i].set_ydata(self.plotBLines[i])

                if self.PLOT_C:
                    for i in range(self.size):
                        self.plotCLines[i].rotate(-1)
                        self.plotCLines[i][self.Xaxis-1] = self.newCValues[i] 
                        self.cPlot[i].set_ydata(self.plotCLines[i])


                if self.PLOT_D: 
                    for i in range(self.size):
                        self.plotDLines[i].rotate(-1)
                        self.plotDLines[i][self.Xaxis-1] = self.newDValues[i] 
                        self.dPlot[i].set_ydata(self.plotDLines[i])


                """-----------------------------------------------------------------------------------------------------------------------------"""
             
                self.canvas.show()
                if self.verbose:
                        print 'Time taken in Plot Loop: ' + format(time.time() - startTime)
                        startTime = time.time()
            
            print "Exit Plot"