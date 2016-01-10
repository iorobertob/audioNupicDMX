

import pyaudio
import numpy

class AudioStream:

    def __init__(self, sr, bufferSize, bitRes, verbose):

        self.daemon = True

        """
        Sampling rate of this sound device, size and resolution of buffers and initial values
        """
        self.audioStarted   = 0
        self.verbose        = verbose
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
        TODO: Change string to use parameter to set this
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
        Open the Audio Stream. Start separate thread
        """    
        self.inStream = p.open(format   = p.get_format_from_width(width, unsigned=False),
                               channels =1,
                               rate     =self.rate,
                               input    =True,
                               frames_per_buffer=self.bufferSize,
                               stream_callback  = callback)
                                                                                                                                   
                                                                                                                                           
    def fft(self, audio):
            """
            Fast Fourier Transform 'output' contains the strength of each frequency in the audio signal
            """
            left = numpy.abs(numpy.fft.fft(audio))
            output = left
            return output

