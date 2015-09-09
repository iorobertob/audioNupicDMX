import numpy
import pyaudio
import serial

CHUNK = 1024
"""
WIDTH --> 2 bytes (16 bit sample)
"""
WIDTH = 2
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = .5
CHUNKSTORECORD=int(RATE*RECORD_SECONDS/CHUNK)
"""
PYAUDIO
"""
p = pyaudio.PyAudio()
rec = numpy.empty((CHUNKSTORECORD*CHUNK),dtype="uint16")
"""
SERIAL COM
"""
ser = serial.Serial('COM5', 57600)
print ("Opening serial port...")
"""
format --> paInt16
"""
#format = p.get_format_from_width(WIDTH, unsigned=True)

stream = p.open(format = p.get_format_from_width(WIDTH, unsigned=True),
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=CHUNK)

print("* recording")

try:
    for i in range(CHUNKSTORECORD):
        #recOutput = numpy.fromstring(stream.read(CHUNK), dtype=numpy.uint16)
        #rec = recOutput
        """
        READ FROM MIC
        """
        rec = stream.read(CHUNK)
        print rec
        """
        WRITE COM PORT
        """
        ser.write(rec)
    #data = stream.read(CHUNK)
    #stream.write(data, CHUNK)
except KeyboardInterrupt:
    pass

print("* done")
"""
CLOSE STREAM AND COM PORT
"""
stream.stop_stream()
stream.close()
ser.close()
