

########################################################################################################
"""
C O N T R O L S
"""
VERBOSE             = 1
ANOMALY_THRESHOLD   = 0.9   # To report when an anomaly exceeds a value. Not implemented.
#-------------------------------------------------------------------------------------------------------
AUDIO               = 1     # Audio module ON/OFF
SR                  = 8000  # Sample Rate of the audio input. 
BITRES              = 16    # Bit Resolution 
BUFFERSIZE          = 2**6  #127
FREQPERBIN          =  int(SR/BUFFERSIZE)   # Frequencies in each bin of the FFT
NOBINS              = 4     # How many frequencies to use for the models
INDEXES             = [
int(500/FREQPERBIN),
int(1000/FREQPERBIN),
int(2000/FREQPERBIN),
int(3000/FREQPERBIN),
]                           # The idexes of the FFT array what has the frequencies of interest. 
FREQS               = 4
GATE                = 40    # Noise Gate Threshold
#-------------------------------------------------------------------------------------------------------
FILES               = 1     # PLAY WAV FILES 
WAV_FILES           = []    # Empty array to later hold the names of the wav files. 
WAV_MINUTES         = 0.01  # The minutes in between triggering the wav files.
#-------------------------------------------------------------------------------------------------------
HTM                 = 1     # HTM   module ON/OFF
HTMHERTZ            = 10    # Model computes per second
#-------------------------------------------------------------------------------------------------------
DMX                 = 1     # DMX   module ON/OFF
SERIAL_PORT         = ''    # Serial port the DMX is connected to
DMX_GAP             = 7     # Space between first address from fixture to fixture
DMX_NUMBER          = 6     # Number of fixtures to use.
DMX_OFFSET          = 1     # Channel number of RED in each Fixture
CYCLE               = 0     # CYCLE+R, CYCLE+G, CYCLE+G, CYCLE increments and wraps around 255
RGB                 = [0] * DMX_GAP * 3    # Array to hold RGB values
BRIGHTENESS         = 1.0   # Range[0.0,1.0]
#-------------------------------------------------------------------------------------------------------
PLOT                = 0     # Plot  module ON/OFF
PLOT_WIDTH 			= 100 	# 
#-------------------------------------------------------------------------------------------------------
START               = 0     # Start the execution of the secondary Thread after the Tkinter
MODEL_RUN           = 1     # Start the processing loop
PAUSE               = 1     # Pause the processing loop
#######################################################################################################
