

import threading

import matplotlib.pyplot as plt
from matplotlib.pyplot   import *
from collections import deque

class Visualizations(threading.Thread):
    
    def __init__(self, xAxis, freqPerBin, noBins, indexes, verbose):

        threading.Thread.__init__(self)
        self.daemon = True

        self.verbose            = verbose

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

