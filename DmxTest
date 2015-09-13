#-------------------------------------------------------------------------------
# Name:        DmxTest1
# Purpose:
#
# Author:      jortega
#
# Created:     10/09/2015
# Copyright:   (c) jortega 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import serial
import time

DmxBufferToSend = [0x00,0x26,0x27,0x55,0xAA,0x26,0x01,0x01]

ser = serial.Serial('COM20',250000)  # open first serial port

#configure 2 stop bits for DMX spec
ser.setStopbits(2)

# configure parity, to set the firs bit alwasy to 0 by Dmx protocol
ser.setParity(serial.PARITY_MARK)

#512 channels + bytes start (byte with O's)
DMX_BUFER_SIZE = 513

# Fill the rest of the buffer with 0's
DmxBufferToSend.extend([0]*(DMX_BUFER_SIZE - len(DmxBufferToSend) ))

# Clear the output
ser.flushOutput()

#
# the program will send Dmx packets until Ctrl C key is press
#
print "Press Ctrl-C to stop the programm"
try:
    while True:
        #send break condition
        ser.sendBreak(0.000001)
        # Write all Dmx Buffer
        ser.write(DmxBufferToSend)
        # clean the output
        ser.flushOutput()
        # sleep 1 ms before to attemp other message
        time.sleep(0.001)
except KeyboardInterrupt:
    pass

# close the port
ser.close()
print "end of program"
