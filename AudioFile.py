
import pyaudio
import wave     
import threading

class AudioFile(threading.Thread):    

    def __init__(self,file, verbose):

        threading.Thread.__init__(self)
        self.daemon = True

        self.verbose= verbose

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
