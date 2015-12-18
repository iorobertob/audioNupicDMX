
import serial
import threading
import math

class PyDMX(threading.Thread):
    """
    D M X  Class for Enttec USB Pro serial porotocol.
    Select the name of the usb port, use baud rate of 57600
    fills an array with the Enteec protocol, 512 channels,
    taking the anomaly value from the Main Thread and using it 
    as chanell value.
    """
    def __init__(self, fixnumber, length, dmxOffset, gap, rgb, serialPort, verbose):
                  
        threading.Thread.__init__(self)
        self.daemon     = True
        
        # Flags and Logic
        self.DMX            = 1
        self.FIXTURENUMBER  = fixnumber
        self.CYCLE          = 0
        self.BRIGHTNESS     = 1.0
        self.verbose        = verbose


        # DMX setup and Data
        self.SERIAL_PORT= serialPort
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
            self.ser = serial.Serial(port=self.SERIAL_PORT, baudrate=57600, timeout=1)
        
        except:
            print "dmx_usb.__init__: ERROR: Could not open %u" % (self.SERIAL_PORT)
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
                    if self.verbose:
                        print "Set Channel " + str(channel) + " to " + str(colour)

            
            #Send data to Enttec Device
            self.update_channels()
        
        #Clear Output, set all channels to 0's
        print 'Out of dmx'

        DMX = 0
        self.blackout()
        self.close_serial()
        self.stop()

