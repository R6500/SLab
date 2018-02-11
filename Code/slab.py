'''
Base SLab Python module
It contains all interaction to the Hardware Board through Base Commands

History:

Version 1.0 : First version

17/2/2017 : It seems that DAC output is more acurate
            than ADC input. 
            ADC can be calibrated against DAC.
            
10/2/2018 : Addition to halt response code            
'''
 
###################### INFO FOR THE HELP FILE ###################################

'''
@root@
This is the main page of the SLab help
List of command category topics:

   manage : System management
     file : File commands
     base : Base DC voltage operations
   plotdc : DC curves
     plot : Generic plot commands
     tran : Transient commands
     wave : Wave commands
     util : Utility commands
      dio : Digital I/O
      cal : Board calibration
      var : Internal variables
      
List of SLab submodule category topics:

       dc : DC submodule
       ac : AC submodule
     meas : Measure submodule
      fft : FFT submodule
       ez : Easy submodule
	  
You can also input the name of a particular command
@manage@  
List of management command topics:

  connect
  disconnect
  softReset
  printBoardInfo
  wait
  pause
  setVerbose
  setPlotReturnData
@file@
  save
  load  
  setFilePrefix
  setCalPrefix  
@base@
List of base DC voltage command topics:

  setVoltage
  readVoltage
  rCurrent
  dcPrint
  dcLive
  zero
  dcSweep
  dcSweepPlot
  writeDAC
  readADC  
  setDCreadings
@plot@
List of generic plotting command topics:

  plot11
  plot1n
  plotnn
@tran@
List of transient command topics:

  setSampleTime
  setTransientStorage
  tranStore (alias)
  tranAsyncPlot
  tranTriggeredPlot
  stepPlot
  transientAsync
  transientTriggered
  stepResponse
@wave@
List of wave command topics:

   waveSquare
   waveTriangle
   waveSawtooth
   waveSine
   waveCosine
   wavePulse
   waveNoise
   waveRandom
   loadWavetable
   setWaveFrequency
   wavePlot
   waveResponse
   singleWavePlot
   singleWaveResponse
   wavePlay
@util@  
List of utility command topics:

   highPeak
   lowPeak
   peak2peak
   halfRange
   mean
   std
   rms
@dio@
List of digital I/O command topics:

   dioMode
   dioWrite
   dioRead   
@cal@
Full board calibration is a four stage procedure
List of calibration command and alias topics:

  Stage 1 : manualCalibrate   | cal1
  Stage 2 : adcCalibrate      | cal2
  Stage 3 : dacCalibrate      | cal3
  Stage 4 : checkCalibration  | cal4
 
 setVdd
 setVref
@var@
List of internal variables topics:

  vdd
  vref
  sampleTime
  linux  
'''

'''
Help information about internal variables
@vdd@
vdd
Voltage supply in Volt
Do not modify this variable
@vref@
vref
Voltage reference in Volt for DACs and ADCs
Do not modify this variable
@sampleTime@
Current sample time in seconds
Do not modify this variable
@linux@
True if system is detected as Linux
Modify before connect if autodetect fails
'''

################################################################################# 
 
import sys            # System module
import time           # Time module for wait
import serial         # Serial connection module
import pickle         # Savedata for calibration
import math           # Math module
import numbers        # Numbers module
import glob
import warnings       # Warnings module

##################### LINUX CHECK ################################

'''
We need to check if we are in Linux because the connection
procedure has specific requirements in Linux

If Linux detection does not work ok, we can force this
variable using:

slab.linux = True    # Linux system
slab.linux = False   # Non Linux system
'''

if sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
    linux = True
else:
    linux = False

#################### SCIPY LOAD ##################################    
    
# Try to load the SciPy modules
# The "TkAgg" backend is selected out of linux because in default
# operation the console goes very slow after plotting
try:		
    import matplotlib
    if not linux:
       matplotlib.use("TkAgg")    
    import numpy as np                # Numpy for math calculations
    import pylab as pl                # Pylab and Mathplotlib for plotting
    import matplotlib.pyplot as plt

except:
    scipy = False
else:
    scipy = True
	   
# Version information
version_major = 1
version_minor = 0
version_date  = "10/2/2018"

# Default baud rate
BAUD_RATE = 38400

# Serial constants
ACK = 181     # Command Ok
NACK = 226    # Command Error
ECRC = 37     # Error in CRC

# External files
HELP_FILE = "SLab_Help.dat"

LAST_COM_FILE = "Last_COM.dat"
ADC_CAL_FILE = "Cal_ADC.dat"
DAC_CAL_FILE = "Cal_DAC.dat"
VDD_CAL_FILE = "Cal_Vdd.dat"

# External files prefixes
fprefix = ""
calprefix = ""

# Exception code
class SlabEx(Exception):
    # Exception Methods ----------------------------------
    def __init__(self, msg=""):
        self.msg = msg
        print "\n** SLab exception"
        print '** ' + msg 
        print "\n"    
        if not interactive:
            raw_input("Hit RETURN to end the script")
            
    def __str__(self):
        return repr(self.code)

# Variable that indicates if plot functions shall return data
plotReturnData = False        
        
# Verbose level 0 = None, 1 = Warn, 2 = Normal, 3 = Extensive
verbose = 2           

# Warn information
nwarns = 0  # No warnings yet        
        
# Warn code
def warn(message):
    global nwarns
    if verbose > 0:
        print "\n** WARNING"
        print "** " + message
        print 
    nwarns = nwarns + 1
                
# Board specific data        
ndacs = 2                         # Default number of available DACs

adcNames = ["ADC1","ADC2","ADC3","ADC4"]  # Names of ADCs
dacNames = ["DAC1","DAC2","DAC3"]         # Names of DACs
        
magic = [56,41,18,1]  # Magic identification code

opened = 0            # Connection not opened yet

vdd = 3.3             # By default vdd is 3.3V
vref = 3.3            # By default vref is 3.3V

dcroundings = 10      # Number of measurements to average in DC

sampleTime = 0.001    # Current sample time

# Default values to be loaded from board
min_sample = 50e-6
max_sample = 1.0

# Empty ADC Calibration tables
xcal  = []
ycal1 = []
ycal2 = []
ycal3 = []
ycal4 = []
adcCalData = [ycal1,ycal2,ycal3,ycal4]

# Empty DAC Calibration tables
dacx  = []
dac1y = []
dac2y = []
dac3y = []
dac4y = []
dacCalData = [dac1y,dac2y,dac3y,dac4y]

# Wavetable information

w_idle = -1  # No wave loaded
w_points = 0 # Number of wave points

# Secondary wavetable information
w_idle2 = -1  # No secondary table loaded
w_points2 = 0 # Number of wave points

# Saturation limits
#SAT_HIGH = 0.95
#SAT_LOW  = 0.05

##################### PUBLIC VARIABLES ###########################

# Trigger Modes
tmodeRise = 0
tmodeFall = 1

# DIO Modes
mInput     = 10
mPullUp    = 11
mPullDown  = 12
mOutput    = 20
mOpenDrain = 21

######################## OBJECTS #################################

'''
bunch (Not used yet)
Generate a new namespace
Included in slab.py 

Example:
  data = bunch(a=1,b=[2,3])
  data.a
  data.b.append(7)
  data.c = "New element"
  data
      
class bunch(dict):
    def __init__(self,**kw):
        dict.__init__(self,kw)
        self.__dict__.update(kw)
'''   
        

####################### PRIVATE SERIAL ###########################

'''
Compose a u16 value from two byes: low and high
Parameters:
  low  : Low byte
  high : High byte
Returns composed valuie
'''    
def composeU16(low,high):
    value = low + high*256
    return value     
   
'''
Split a u16 value in two byes: low and high
Parameters:
  data : value to convert
Returns low,high
'''    
def splitU16(data):
    high = data//256
    low = data % 256
    return low,high   
   
'''
Start of a Tx transmission
'''   
def startTx():
    global crcTx
    crcTx = 0
    
'''
Send the crc
Usually that ends the Tx transmission
'''    
def sendCRC():
    global crcTx
    ser.write(chr(crcTx))
    
'''
Send one byte and computes crc
'''    
def sendByte(byte):
    if byte < 0 or byte > 255:
        raise SlabEx("Byte value out of range")
    global crcTx
    ser.write(chr(byte))
    crcTx = crcTx ^ byte
   
'''
Send one uint16 and computes crc
'''   
def sendU16(value):
    if value < 0 or value > 65535:
        raise SlabEx("Unsigned 16 bit integer out of range")
    low,high = splitU16(value)
    sendByte(low)
    sendByte(high)  
  
'''
Send one float and computes crc
Floats are sent as an offset 128 exponent (1 byte)
followed by an offset 20000 4 digit mantissa (2 byte U16)
Returns the sent float value
'''
def sendFloat(value):
    # Convert to mantissa/exponent
    exp  = int(math.floor(math.log10(value)))-3;
    mant = int(value/math.pow(10,exp))
    sendByte(exp+128)
    sendU16(mant+20000)
    # Recalculate value
    value2 = 1.0 * mant * math.pow(10,exp)
    return value2
    
'''
Start of a Rx reception
'''   
def startRx():
    global crcRx
    crcRx = 0
    
'''
Get CRC anc check it
It usually ends the Rx reception
'''    
def checkCRC():
    global crcRx
    crc = ord (ser.read())
    if crc != crcRx:
        raise SlabEx("CRC Error in Board to PC link")
   
'''
Get one byte and computes crc
'''   
def getByte():
    global crcRx
    byte = ord (ser.read())
    crcRx = crcRx ^ byte
    return byte
    
'''
Get one uint16 and computes crc
'''    
def getU16():
    low  = getByte()
    high = getByte()
    value = composeU16(low,high)
    return value 
 
'''
Get one float value and computes crc
''' 
def getFloat():
    # Get exponent and mantissa
    exp = getByte() - 128
    mant = getU16() - 20000
    # Compute value
    value = 1.0 * mant * math.pow(10,exp)
    return value    
   
'''
Check ACK, NACK and ECRC
'''   
def checkACK():
    # Get response
    response = getByte();    
   
    if (response == NACK) or (response == ECRC):
        # Check also CRC
        checkCRC()
        # Exceptions
        if (response == NACK):
            raise SlabEx("Remote Error : Bad command parameters")
        
        if response == ECRC:
            raise SlabEx("CRC Error in PC to Board link")
        
    if response != ACK:
        raise SlabEx("Unknown Board Response")   
    
'''
Start command
Parameters:
   code : Code of command
'''
def startCommand(code):
    startTx()
    startRx()
    sendByte(ord(code))
    

'''
Check Magic 
Check magic code in an opened serial connection
returns 1 if board is correct or 0 otherwise
'''
def checkMagic():
    global ser
    
    # First we flush
    ser.flushInput()
    
    startCommand('M') # Magic request
    sendCRC()         # End of command
        
    # Check that it responds if not Linux
    if not linux:
        time.sleep(0.1)
   
        if ser.inWaiting() < 5 :
	        return 0
    
    read = getByte()
    if read != ACK:
        return 0
    
    # Check all magic bytes
    for char in magic:
        # Obtain the byte value of received character 
        read = getByte()
        # Exit if the magic does not match
        if read != char:
            return 0
       
    # Check CRC
    checkCRC()
       
    # If we arrive here, magic is good
    return 1    

'''
Open a serial connection with the given port
Includes the Linux especific operations
'''    
def openSerial(com_port):
    global ser
    ser = serial.Serial(port=com_port,baudrate=BAUD_RATE)
    # Settings required for Linux in the Nucleo boards
    if linux: 
        ser.setDTR(False)
        ser.setRTS(True)
    
'''
Detect and open COM port
Only returns if the board is detected
'''
def detectCom():
    global ser
    global com_port
    
    # Check if there is a saved last port
    try:
        with open(fprefix + LAST_COM_FILE) as f:
            com_port = pickle.load(f) 
    except:
        pass
    else:
        try:
            message(1,"Trying last valid port " + str(com_port))
            openSerial(com_port)
        except:
            pass
        else:    
            if checkMagic():
                message(1,"Board detected")
                return   
        message(1,"Last used port is not valid")
        message(1,"Searching for port")
    
    # Get a list of ports to tests
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise SlabEx('Platform not supported in autodetect')
            
    # Test each port    
    for p in ports:
        try:
            message(2,"Testing port " +str(p))
            # Port to try
            openSerial(p)
            
            if checkMagic():
                message(1,"Board detected at port " + str(p))
                com_port = p
                return
            ser.close()
        except (OSError, serial.SerialException):
            pass
    raise SlabEx('COM Autodetect Fail')    

    
#################### PRIVATE FUNCTIONS ###########################

'''
Convert a U16 value in float
Truncates to the limits
Parameter:
  value : U16 value between 0 an 65535
Returns float between 0.0 and 9.9998
'''   
def u16toFloat(value):
    if value < 0:
        value = 0
    if value > 65535:
        value = 65535
    return value / 65536.0
   
'''
Convert a float value to U16
Truncates in the limits
Parameter:
  value : Float value between 0.0 and 9.9998
Returns u16 between 
'''   
def floatToU16(fvalue):
    value = int(fvalue*65536.0)
    if value < 0:
        value = 0
    if value > 65535:
        value = 65535
    return value    

'''
Send a message to screen
Parameters:
    level : 1 Normal for verbose 2
            2 Extensive for verbose 3
'''
def message(level,message):
    # Check level errors    
    if level < 1 or level > 2:
        raise SlabEx("Internal Error : Bad message level")
    # Print message depending on level    
    if level < verbose:
        print(message)
        
'''
Calibrates one reading 0.0...1.0
Returns real ratiometric from read ADC ratiometric 
If data is outside of the calibration table, it returns 
the data without any calibration.
Parameters:
  input  : Float value to calibrate in table2 domain
  list1 : List of correct values
  list2 : List of incorrect values
Returns the calibrated value
'''  
def dc_cal(input,list1,list2):  
    if len(list1) < 2:
        return input
    prevx = -1.0   # Lower limit for x (calibrated)
    prevy = -1.0   # Lower limit for y (uncalibrated)
    for x,y in zip(list1,list2):
        if input <= y:         # Locate upper limit
            if prevx == -1:    # If out of table...
                return input   # ...don't calibrate
            # Calbrate the value    
            alpha = (input - prevy)/(y - prevy)
            value = prevx + alpha*(x - prevx)
            return value            
        else:
            prevx = x    # New lower limit
            prevy = y
    # Don't calibrate if we are out of the table        
    return input 
      
'''
Get firmware string
This command don't use CRC
'''    
def getFirmwareString():
    startCommand('F')

    cad = "" 

    # Check that it responds if not Linux
    if not linux:
        time.sleep(0.2);
        nchar = ser.inWaiting()
        if nchar < 1 :
            return "Unknown"
   
        for i in range(0,nchar):
            car = ser.read()
            if (not car == '\n') and (not car == '\r'):
                cad = cad + str(car)
        return cad        
    else:
        car = ser.read()
        while not car == '\n':
            cad = cad + str(car) 
            car = ser.read()
        ser.read() # Flush '\r'
        return cad     
   
'''
Read one pin name
'''
def readPinName():
    name = ""
    while True:
        car = chr(getByte())
        if car == '$':
            raise SlabEx("Unexpected end of pin list")
        if car == '|':
            return name        
        name = name + str(car)    
   
'''
Identifies the connected board
'''
def getBoardData():
    global board_name
    global ndacs,nadcs,buff_size,max_sample,min_sample,vdd
    global dacPinList,adcPinList,dioPinList
    global maxSFfresponse
    global vref,dac_bits,adc_bits
    global ndio
    
    print "Getting board data"
    
    # Get firmware string
    board_name = getFirmwareString()
    message(1,"Connected to " + board_name)
    
    startCommand('I')  # Get board capabilities
    sendCRC()          # End of command
    
    # Check response
    time.sleep(0.1)
    flush = 0
    if not ser.inWaiting() == 25:   # Data size + 2 (ACK and CRC)
        message(1,"Unexpected Board Data")
        flush = 1
    # Check ACK    
    checkACK()    
    # Get data
    ndacs = getByte()
    nadcs = getByte()
    buff_size = getU16()
    max_sample = getFloat()
    min_sample = getFloat()  
    vdd  =  getFloat()
    maxSFfresponse = getFloat()
    vref = getFloat()
    dac_bits = getByte()
    adc_bits = getByte()
    ndio = getByte()
    rState = getByte()
   
    if flush:
        # Flush buffer
        ser.flushInput()
    else:
        checkCRC()
    
    if rState:
        message(1,"Board at reset state")
    else:
        message(1,"Board out of reset state")
    
    # Get pin list
    dacPinList=[]
    adcPinList=[]
    dioPinList=[]
    startCommand('L')
    sendCRC()          # End of command
    
    checkACK()
    for i in range(0,ndacs):
        dacPinList.append(readPinName())
    for i in range(0,nadcs):
        adcPinList.append(readPinName()) 
    for i in range(0,ndio):
        dioPinList.append(readPinName())         
            
    # Get the final $
    car = chr(getByte())
    if car != '$':
        raise SlabEx("[P] Bad termination in pin list")
           
    checkCRC()
    # Flush buffer
    ser.flushInput()
   
'''
Ratiometric read of one analog ADC channel
Does not perform any calibration
Parameters:
   n :Channel can be a number 1,2,3,4
Returns the ratiometric reading between 0.0 and 1.0   
'''    
def readChannel(n):
    if not opened:
        raise SlabEx("Not connected to board")
    if n > nadcs:
        raise SlabEx("Invalid ADC number")        
    acum = 0.0     
    '''
    # This code has been moved to the hardware board
    for i in range(0,dcroundings):
        startCommand('A')
        sendByte(n);
        sendCRC()          # End of command
        
        checkACK()
        value = getU16()
        checkCRC()
        
        fvalue = u16toFloat(value)
        acum = acum + fvalue
    fvalue = acum / dcroundings 
    '''
    startCommand('A')
    sendByte(n);
    sendCRC()          # End of command
        
    checkACK()
    value = getU16()
    checkCRC() 
    
    fvalue = u16toFloat(value)
    
    return fvalue  
	
'''
Ratiometric write of one analog DAC channel
Does not perform any calibration
Parameters:
      n : DAC to set 1,2 (or 3 if three DACs)
  value : Value to set 0.0 to 1.0
'''    
def writeChannel(n,value):
    if not opened:
        raise SlabEx("Not connected to board")
    if n > ndacs:    
        raise SlabEx("Invalid DAC number")        
    data = ratio2counts(value)
    
    startCommand('D')
    sendByte(n)
    sendU16(data) 
    sendCRC()
    
    checkACK()
    checkCRC()

'''
Convert ratiometric level to counts
Generate exception if out of range
Parameter:
   ratio : Value between 0.0 and 1.0
Returns uint 16   
'''  
def ratio2counts(ratio):
    if ratio < -0.001:
        raise SlabEx("Ratiometric value cannot be below 0.0")
    if ratio > 1.001:
        raise SlabEx("Ratiometric value cannot be above 1.0")

    data = floatToU16(ratio)
            
    return data    

'''
Convert voltage value to ratiometric value
'''    
def voltage2ratio(value):
    if value < -0.001:
        raise SlabEx("Voltage value cannot be below 0 V")
    if value > vref*1.001:
        raise SlabEx("Voltage value cannot be above Vref")
    return value/vref;
    
'''
Convert voltage value to counts 
'''  
def voltage2counts(value):
    return ratio2counts(voltage2ratio(value))
       
'''
Message when SciPy is not loaded and we cannot plot
'''       
def cannotPlot(exception=False):
    if not exception:
        message(1,"")
        message(1,"SciPy not loaded. Cannot plot")
        message(1,"")
    else:
        raise SlabEx("SciPy not loaded. Cannot plot")
       
'''
Generate an exception if scipy is not loaded
'''  
def checkSciPy():
    if not scipy:
        raise SlabEx("SciPy not loaded. Cannot execute")
       
#################### HELP CODE ###########################       

'''
@help@
help(topic)
Gives help information

Optional parameters:
   topic : Text to give information about
           (Defaults to "root")
Returns nothing
Included in slab.py           
'''
def help(topic="root"):
    while (True):
        print
        ftopic = "@"+topic+"@"
        topic_found = False
        list = []
        maxlen = 0
        with open(fprefix + HELP_FILE, 'r') as hfile:
            for line in hfile:
                if line.startswith("#"):
                    continue
                if not topic_found:
                    if line.startswith("@#"):
                        print "'" + topic + "' topic not found"
                        break
                    elif line.upper().startswith(ftopic.upper()):
                        topic_found = True
                else:
                    if line.startswith("@"):
                        break
                    list.append(" " + line[0:-1]) 
                    if len(line) > maxlen:
                        maxlen = len(line)
                    # print " " + line[0:-1]
        if topic_found:            
            print (maxlen+1)*"-"
            for line in list:
                print line
            print (maxlen+1)*"-"
        else:
            print        
        print "root topic goes to main page"
        print "Just hit return to exit help"
        print
        topic = raw_input("Help topic : ")
        if topic == "":
            print
            return
       
############# PUBLIC NO BOARD RELATED FUNCTIONS #################
    
'''
@wait@
wait(t)
Wait the indicated time in seconds

Required parameter:
    t : Time to wait in float seconds
Returns nothing
Included in slab.py 
'''    
def wait(t):
    time.sleep(t)
    
'''
@pause@
pause(message)
Pause the script untill return is hit

Optional parameter:
  message : Message to show 
            (Use default if not provided)
Returns nothing 
Included in slab.py            
'''    
def pause(message="Script Paused. Hit RETURN to continue"):
    raw_input(message)
    
    
'''
@setVerbose@
setVerbose(level)
Sets the verbose level

Required parameter:
   level : Verbose level 0, 1, 2 or 3
           0 : No messages
           1 : Only warnings
           2 : Basic information
           3 : Detailed information
Returns previous verbose level 
Included in slab.py   
'''    
def setVerbose(level):
    global verbose
    # Check
    if level < 0 or level > 3:
        raise SlabEx("Invalid verbose level")
    # Set level
    last_verbose = verbose
    verbose = level    
    return last_verbose
    
'''
@setFilePrefix@
setFilePrefix(prefix)
Set file prefix for all external files

Optional parameter:
  prefix : Prefix to use (Defaults to none)
Returns nothing  
Included in slab.py 

See also setCalPrefix
''' 
def setFilePrefix(prefix=""):
    global fprefix
    fprefix = prefix
    
'''
@setCalPrefix@
setCalPrefix(prefix)
Set file prefix for calibration files
It adds after file prefix if present

Optional parameter:
  prefix : Prefix to use (Defaults to none)
Returns nothing  
Included in slab.py 

See also setFilePrefix
''' 
def setCalPrefix(prefix=""):
    global calprefix
    calprefix = prefix    
    
    
'''
@save@
save(filename,data)
Saves a variable on a file
Adds .sav extension to filename

Parameters:
  filename : Name of the file (with no extension)
  data : Variable to store
  
Returns nothing  
Included in slab.py 
'''    
def save(filename,data):
    with open(filename+".sav",'wb') as f:
        pickle.dump(data,f)
    message(1,"Data saved")

'''
@load@
load(filename)
Loads a variable from a file
Adds .sav extension to filename

Parameters:
  filename : Name of the file (with no extension)
  
Returns variable contained in the file
Included in slab.py 
'''    
def load(filename):
    with open(filename+".sav") as f:
        data = pickle.load(f)
    message(1,"Data loaded")    
    return data
    
################ PUBLIC BASIC DC FUNCTIONS ####################

'''
@printBoardInfo@
printBoardInfo()
Shows board information on screen
Returns nothing
Included in slab.py 
'''
def printBoardInfo():
    if not opened:
        raise SlabEx("No board connected")
    print ""
    print "Board : " + board_name
    print "  COM port : " + str(com_port)
    print "  Reference Vref voltage : " + str(vref) + " V"
    print "  Power Vdd voltage : " + str(vdd) + " V"
    print "  " + str(ndacs) + " DACs with " + str(dac_bits) + " bits"
    print "  " + str(nadcs) + " ADCs with " + str(adc_bits) + " bits"
    print "  " + str(ndio) + " Digital I/O lines"
    print "  DAC Pins " + str(dacPinList)
    print "  ADC Pins " + str(adcPinList)
    print "  DIO Pins " + str(dioPinList)
    print "  Buffer Size : " + str(buff_size) + " samples"
    print "  Maximum Sample Period : " + str(max_sample) + " s"
    print "  Minimum Sample Period for Transient Async: " + str(min_sample) + " s"
    print "  Maximum Sample Frequency for Frequency Response : " + str(maxSFfresponse) + " Hz"
    print ""
 
  
'''
@disconnect@
disconnect()
Disconnect from the board
Returns nothing
Included in slab.py 
'''  
def disconnect():
    global opened
    if not opened:
        raise SlabEx("Not connected to board")
    ser.close()
    opened = 0
    message(1,"Disconnected from the board")
    if nwarns > 0:
        message(1,str(nwarns) + " warnings since connect")
  
 
'''
@connect@
connect(portIdent)
Open the connection with the hardware board
Must be called before any other function that uses it

Optional parameter:
   portIdent : Identifier of the COM port 
               In windows it is COMx where x is a number
               (Defaults to Autodetect)
Returns nothing
Included in slab.py 
'''
def connect(portIdent=-1):
    global ser,opened
    global xcal,ycal1,ycal2,ycal3,ycal4,adcCalData
    global dacx,dac1y,dac2y,dacCalData
    global com_port
    global vdd,vref
    global nwarns
    
    # Check if already connected
    if opened:
        message(1,"Already connected")
        disconnect()
    
    com_port = portIdent
        
    if portIdent == -1:
        detectCom()
    else:    
        try:    
            openSerial(com_port)
        except:
            raise SlabEx("Cannot open connection. Check port")
    
    if not ser.isOpen():
        raise SlabEx("Cannot open connection. Check port")
         
    # Get firmware string
    #board_name = getFirmwareString()
    #message(1,"Connected to " + board_name)

    if not checkMagic(): 
        raise SlabEx("Bad magic from board. Check Firmware")
            
    # Set board as opened
    opened = 1    
    
    # Save good com port
    with open(fprefix + LAST_COM_FILE,'wb') as f:
        pickle.dump(com_port, f)
    
    # Get information about the board
    getBoardData()
                    
    # Try to load ADC calibration data
    try:
        with open(fprefix + calprefix + ADC_CAL_FILE) as f:
            xcal,ycal1,ycal2,ycal3,ycal4 = pickle.load(f) 
    except:
        message(1,"No ADC calibration data found")
    else:
        message(1,"ADC Calibration data loaded")
        # All output adc calibration tables    
        adcCalData = [ycal1,ycal2,ycal3,ycal4]
        
    # Try to load DAC calibration data
    try:
        with open(fprefix + calprefix + DAC_CAL_FILE) as f:
            dacx,dac1y,dac2y,dac3y,dac4y = pickle.load(f) 
    except:
        message(1,"No DAC calibration data found")
    else:
        message(1,"DAC Calibration data loaded")
        # All output dac calibration tables    
        dacCalData = [dac1y,dac2y,dac3y,dac4y]        
        
    # Try to load Vdd and Vref calibration data
    try:
        with open(fprefix + calprefix + VDD_CAL_FILE) as f:
            vdd,vref = pickle.load(f)
    except:
        pass
    else:
        message(1,"Vdd loaded from calibration as " + str(vdd) + " V")
        message(1,"Vref loaded as " + str(vref) + " V")
  
    message(1,"")
    
    # Erase warn count
    nwarns = 0

'''
@setVdd@
setVdd(value,persistent)
Set Vdd supply voltage

Required parameter:
  value : Value to set (in Volt)
  
Optional parameter:
  persistent : Makes value persistent in a file
               (Defaults to False)

Returns nothing  
Included in slab.py              
'''  
def setVdd(value,persistent=False):
    global vdd
    # Check connection
    if not opened:
        raise SlabEx("Not connected to board")
    # Check vdd value
    if value < 3.0:
        raise SlabEx("Vdd value too low")
    # Removed to expand functionality at high voltages    
    # if value > 4.0:
    #    raise SlabEx("Vdd value too high")
    vdd = value
    
    # Save if persistent
    if persistent:
        message(1,"Saving Vdd and Vref data to " + fprefix + calprefix + VDD_CAL_FILE)
        with open(fprefix + calprefix + VDD_CAL_FILE,'wb') as f:
            pickle.dump([vdd,vref], f)
            
'''
@setVref@
setVref(value,persistent)
Set Vref reference value for DACs and ADCs

Required parameter:
  value : Value to set (in Volt)
  
Optional parameter:
  persistent : Makes value persistent in a file
               (Defaults to False)

Returns nothing
Included in slab.py                
'''  
def setVref(value,persistent=False):
    global vref
    # Check connection
    if not opened:
        raise SlabEx("Not connected to board")
    # Check vref value
    if value < 3.0:
        raise SlabEx("Vref value too low")
    # Removed to expand functionality at high voltages    
    # if value > 4.0:
    #    raise SlabEx("Vref value too high")
    vref = value
    
    # Save if persistent
    if persistent:
        message(1,"Saving Vdd and Vref data to " + fprefix + calprefix + VDD_CAL_FILE)
        with open(fprefix + calprefix + VDD_CAL_FILE,'wb') as f:
            pickle.dump([vdd,vref], f)            
  
'''
@writeDAC@
writeDAC(channel,value)
Write a ratiometric value to one DAC
Performs calibration if available

Required parameteres:
 channel : DAC number
   value : Value to set from 0.0 to 1.0 
Returns nothing
Included in slab.py    
'''  
def writeDAC(channel,value):   
    # Calibrate value    
    value = dc_cal(value,dacx,dacCalData[channel-1])    
    
    # Send to board
    writeChannel(channel,value)  

 
'''
@setVoltage@
setVoltage(channel,value)
Sets the voltage value of one DAC
Performs calibration if available

Required parameters:
 channel : DAC to write
   value : Voltage to set
Returns nothing
Included in slab.py    
'''   
def setVoltage(channel,value):
    value = voltage2ratio(value)
    writeDAC(channel,value)
 

'''
@readADC@
readADC(channel)
Read the ratiometric value at one ADC
Uses calibration data if available

Rquired parameter:
  n : ADC number
Returns a ratiometric value between 0.0 and 1.0
Included in slab.py 
'''            
def readADC(channel):
    fvalue = readChannel(channel)
    return dc_cal(fvalue,xcal,adcCalData[channel-1])  
    
    
'''
@readVoltage@
readVoltage(ch1,ch2)
Reads a differential voltage between two ADCs at ch1 and ch2
If ch2 is ommited, returns voltage between ch1 and GND
If any channel is zero, it is considered as GND
Return the voltage
Included in slab.py 
'''    
def readVoltage(ch1,ch2=0):
    if ch1 == 0:
        pvalue = 0.0
    else:    
        pvalue = vref*readADC(ch1)
    if ch2 == 0:
        nvalue = 0.0
    else:
        nvalue = vref*readADC(ch2)
    return pvalue - nvalue 

'''
@rCurrent@
rCurrent(r,ch1,ch2)
Reads the voltage on a resistor and computes current from it
If any channel is zero, it is considered as GND

Parameters:
   r : Resistor value
  n1 : Positive terminal ADC
  n2 : Negative terminal ADC
       If omited it is considered to be GND
Returns the resistor current 
Included in slab.py       
'''    
def rCurrent(r,ch1,ch2=0):
    v = readVoltage(ch1,ch2)
    i = v/r
    return i
    
'''
@setDCreadings@
setDCreadings(number)
Sets the number of readings to average on each DC mesurement
Parameter:
  number : Number of values to read
Returns last value of this number
Included in slab.py   
'''
def setDCreadings(number):
    global dcroundings
    lastValue = dcroundings
    # Check
    if number < 1:
        raise SlabEx("Number of readings must be greater or equal than 1")
    if number > 65535:
        raise SlabEx("Number of readings too big")
    dcroundings = int(number)
    
    # Send command
    startCommand('N')
    sendU16(dcroundings) 
    sendCRC()
    
    checkACK()
    checkCRC()
    
    return lastValue
   
'''
@adcCalibrate@
adcCalibrate()
Second stage of board calibration
Calibrates ADCs against DAC1
Stores calibration data on ADC_CAL_FILE file
Returns nothing
Included in slab.py 
'''   
def adcCalibrate():
    global xcal,ycal1,ycal2,ycal3,ycal4,adcCalData
    
    print
    print "Calibration of ADCs"
    print
    print "Connect the DAC 1 output to all ADC inputs"
    print "Use the buffers in all connections"
    print    
    raw_input("Press [Return] to continue")
    
    # Increase number of readings for better calibration
    lastDCR=setDCreadings(1000)
    
    # Define input calibration range and steps
    # xcal = np.arange(0.0,1.1,0.1)
    xcal = []
    for x in range(0,11):
        xcal.append(x/10.0)
    
    # Output range is now empty
    ycal1 = []
    ycal2 = []
    ycal3 = []
    ycal4 = []
    
    # Obtain calibration data
    # We use readChannel because it does not depend on
    # previous calibrations
    message(1,"Performing ADC calibration")
    for x in xcal:
        message(2,"  Calibrate at " + str(x))
        writeDAC(1,x)        # Set DAC value
        time.sleep(0.1)      # Wait a little
        a1 = readChannel(1)  # ADC read
        a2 = readChannel(2)
        a3 = readChannel(3)
        a4 = readChannel(4)
        ycal1.append(a1)     # Append values
        ycal2.append(a2)
        ycal3.append(a3)
        ycal4.append(a4)
    
    prev1=-1;
    # Check monotony
    for x,y1,y2,y3,y4 in zip(xcal,ycal1,ycal2,ycal3,ycal4):
        if prev1!=-1:
            if y1 < prev1:
                raise SlabEx("Channel 1 non monotonous")
            if y2 < prev2:
                raise SlabEx("Channel 2 non monotonous")
            if y3 < prev3:
                raise SlabEx("Channel 3 non monotonous")
            if y4 < prev4:
                raise SlabEx("Channel 4 non monotonous")               
        prev1 = y1
        prev2 = y2
        prev3 = y3
        prev4 = y4
    
    # Show graph is we have SciPy
    if not scipy:
        cannotPlot()
    else:    
        plt.figure(facecolor="white")     # White border
        pl.plot(xcal,ycal1,label="ADC1")  # Show curves
        pl.plot(xcal,ycal2,label="ADC2")
        pl.plot(xcal,ycal3,label="ADC3")
        pl.plot(xcal,ycal4,label="ADC4")

        pl.xlabel('DAC1 Value')                         # Set X label
        pl.ylabel('ADC 1,2,3,4 Values')                 # Set Y label
        pl.title('ADC Ratiometric Calibration Curves')  # Set title

        pl.legend(loc='lower right')
        pl.grid()
        pl.show() 
        pl.close()

    # Save of calibration data
    message(1,"Saving calibration data to " + fprefix +  calprefix + ADC_CAL_FILE)
    with open(fprefix + calprefix +  ADC_CAL_FILE,'wb') as f:
        pickle.dump([xcal,ycal1,ycal2,ycal3,ycal4], f)
        
    # All calibration tables    
    adcCalData = [ycal1,ycal2,ycal3,ycal4]    
            
    # Restore the number of ADC readings
    setDCreadings(lastDCR)
            
    print 
    print "Calibration of ADCs completed"
    print    
   
'''
Stores DAC calibration data
Internal function
Parameter:
 n : Number of DACs to show
'''   
def _storeAndShowDACcalibration(n):

    # Plot if we have SciPy
    if not scipy:
        cannotPlot()
    else:    
        plt.figure(facecolor="white")     # White border
        pl.plot(dacx,dac1y,label="DAC1")  # Show curves
    
        if n >= 2:
            pl.plot(dacx,dac2y,label="DAC2")
        if n >= 3:
            pl.plot(dacx,dac2y,label="DAC3")

        pl.xlabel('DAC Value')                          # Set X label
        pl.ylabel('Real Ratiometric Values')            # Set Y label
        pl.title('DAC Ratiometric Calibration Curves')  # Set title

        pl.legend(loc='lower right')
        pl.grid()
        pl.show()   
        pl.close()        

    message(1,"Saving calibration data to "+ fprefix + calprefix + DAC_CAL_FILE)
    with open(fprefix + calprefix + DAC_CAL_FILE,'wb') as f:
        pickle.dump([dacx,dac1y,dac2y,dac3y,dac4y], f)
     
    # All calibration tables    
    dacCalData = [dac1y,dac2y,dac3y,dac4y]       
   
'''
@dacCalibrate@
dacCalibrate()
Third stage of board calibration
Calibrates DAC(i) against ADC(i)
Stores calibration data on DAC_CAL_FILE file
Returns nothing
Included in slab.py 
'''   
def dacCalibrate():
    global dacx,dac1y,dac2y,dac3y,dac4y,dacCalData
    
    print
    print "Calibration of DACs"
    print
    print "Connect the DAC outputs to ADC inputs with same number"
    print "DAC 1 to ADC 1 and DAC2 to ADC2 and son on..."
    print    
    raw_input("Press [Return] to continue")
    
    # Increase number of readings for better calibration
    lastDCR=setDCreadings(1000)
    
    # Define input calibration range and steps
    # dacx = np.arange(0.0,1.1,0.1)
    dacx = []
    for x in range(0,11):
        dacx.append(x/10.0)
    
    # Output range is now empty
    dac1y = []
    dac2y = []
    dac3y = []
    dac4y = []
    
    # Obtain calibration data
    # We use previusly calibrated ADC channels
    message(1,"Performing DAC calibration")
    for x in dacx:
        message(2,"  Calibrate at " + str(x))
        writeChannel(1,x)       # Set DAC values without calibration
        writeChannel(2,x)
        if ndacs >= 3:
            writeChannel(3,x)
        time.sleep(0.1)    # Wait a little
        a1 = readADC(1)    # ADC ratiometric read (with calibration)
        a2 = readADC(2)
        dac1y.append(a1)   # Append read values
        dac2y.append(a2)
        if ndacs>=3:
            a3 = readADC(3)    
            dac3y.append(a3)
    
    prev1=-1;
    # Check monotony
    for x,y1,y2,y3,y4 in zip(xcal,dac1y,dac2y,dac3y,dac4y):
        if prev1!=-1:
            if y1 < prev1:
                raise SlabEx("Channel 1 non monotonous")
            if y2 < prev2:
                raise SlabEx("Channel 2 non monotonous")
            if ndacs >= 3 and y3 < prev3:
                raise SlabEx("Channel 3 non monotonous")
            if ndacs >= 4 and y4 < prev4:
                raise SlabEx("Channel 4 non monotonous")               
        prev1 = y1
        prev2 = y2
        prev3 = y3
        prev4 = y4    
    
    # Show and save calibration data
    _storeAndShowDACcalibration(ndacs)
     
    # Restore the number of ADC readings
    setDCreadings(lastDCR) 
     
    print 
    print "Calibration of DACs completed"
    print     
   
'''
@manualCalibrateDAC1@
manualCalibrateDAC1()
First stage of board calibration
Performs a manual calibration of DAC 1 against a voltage meter
Also calibrates Vdd and Vref
Returns nothing
Included in slab.py 
'''   
def manualCalibrateDAC1():  
    global vdd,vref,dacx,dac1y
    print
    print "Manual calibration of DAC 1"
    print "You will need a voltage measurement instrument (VM)" 
    print
    print "Put VM between the Vdd terminal and GND"
    print "Write down the voltage value and press enter"
    print
    vdd = float(raw_input("Voltage value [Volt]: "))
    print
    print "Put VM between the buffered DAC 1 output and GND"
    print "Write down the voltage value and press enter each time it is asked"
    print
    
    # Increase number of readings for better calibration
    lastDCR=setDCreadings(1000)
    
    dacx  = [0.0,0.02,0.1,0.5,0.9,0.98,1.0]
    voltages = []
    
    prevv = -1.0
    for x in dacx:
        writeChannel(1,x)
        y = float(raw_input("Voltage value [Volt]: "))
        voltages.append(y)
        if y < prevv:
            raise SlabEx("Non monotonous. Cannot calibrate")
        prevv = y
        
    # Stores vdd and vref calibration
    if voltages[3]*2.0 > voltages[6] :
        setVref(voltages[3]*2.0, persistent=True)
    else:    
        setVref(voltages[-1], persistent=True) 

    # Convert to ratiometric    
    dac1y = []
    for v in voltages:
        dac1y.append(v/vref)
        
    # Store calibration
    _storeAndShowDACcalibration(1)  

    # Restore the number of ADC readings
    setDCreadings(lastDCR) 
    
    print 
    print "Manual calibration of DAC 1 completed"
    print    
    

'''
@checkCalibration@
checkCalibration()
Fourth and last stage of board calibration
Checks the board calibration
Shows the curves of DACs connected to ADCs
Returns nothing
Included in slab.py 
'''    
def checkCalibration():

    print
    print "Calibration check"
    print
    print "Connect the DAC outputs to ADC inputs with same number"
    print "DAC 1 to ADC 1 and DAC2 to ADC2 and son on..."
    print "Connect the rest of ADCs to DAC 1"
    print    
    raw_input("Press [Return] to continue")

    # Increase number of readings for better calibration
    lastDCR=setDCreadings(400)
    
    vmin = 0.1
    vmax = vref - 0.1

    R1 = dcSweep(1,vmin,vmax,0.2)
    R2 = dcSweep(2,vmin,vmax,0.2)
    if ndacs > 2:
        R3 = dcSweep(3,vmin,vmax,0.2)

    x = R1[0]
    y1 = R1[1]
    y2 = R2[2]
    if ndacs > 2:
        y3 = R3[3]
    else:
        y3 = R1[3]
    y4 = R1[4]

    for i in range(1,ndacs+1):
        setVoltage(i,1.0)
    
    message(1,"")
    message(1,"DAC outputs shall be now 1V")
    message(1,"They will be zero after closing the plot")
    message(1,"")
    
    plot1n(x,[y1,y2,y3,y4],"Final curves","DAC (V)","ADC (V)",["Ch1","Ch2","Ch3","Ch4"])
    
    zero()
    
    
    # Restore the number of ADC readings
    setDCreadings(lastDCR) 
    
    

'''
@dcPrint@
dcPrint()
Show readings all four ADC channels on screen
Returns nothing
Included in slab.py  
'''
def dcPrint():
    a1 = readVoltage(1);
    a2 = readVoltage(2);
    a3 = readVoltage(3);
    a4 = readVoltage(4);
    print "ADC DC Values"
    print "  ADC1 = "+"{0:.3f}".format(a1)+" V"
    print "  ADC2 = "+"{0:.3f}".format(a2)+" V"
    print "  ADC3 = "+"{0:.3f}".format(a3)+" V"
    print "  ADC4 = "+"{0:.3f}".format(a4)+" V"
    print ""
    
'''
@zero@
zero()
Set all DACs to ratiometric zero
Does not use calibration
Returns nothing
Included in slab.py 
'''    
def zero():
    for i in range(1,ndacs+1):
        writeChannel(i,0.0);  
    message(2,"All DACs at zero")        
  
'''
@dcLive@
dcLive(n,wt,single,returnData)
Prints live values of ADC voltages
Use CTRL+C to exit

Optional parameters:
          n : Number of ADCs to show (Defaults to 4)
         wt : Wait time, in seconds, between measurements (Defaults to 0.2)
     single : Read only the ADC number n
 returnData : Return obtained data

Included in slab.py
'''
def dcLive(n=4,wt=0.2,single=False,returnData=False):
    # Initial checks
    if not opened:
        raise SlabEx("Not connected to board")
    if n < 1 or n > 4:
        raise SlabEx("ADC number out of range")
    
    # Generate output lists
    data=[]
    if not single:
        for i in range(0,n):
            data.append([])
    
    print "Live voltage readings:"
    print
    try:
        while True:
            sys.stdout.write("\r")
            if single:
                a = readVoltage(n)
                sys.stdout.write(" ADC%d: " % n)
                sys.stdout.write("%f V" % a)
                if returnData:
                    data.append(a)
            else:
                for i in range(1,n+1):
                    a = readVoltage(i)
                    sys.stdout.write(" ADC%d: " % i)
                    sys.stdout.write("%f V" % a)
                    if returnData:
                        data[i-1].append(a)
            sys.stdout.write("    ")
            wait(wt)
    except:
        print
        print "End of live measurements"
        print
        
    # Compose return data if enabled    
    if returnData:
        if not scipy:
            return data
        else:    
            if single:
                return np.array(data)
            elif n == 1:
                return np.array(data[0])
            else:
                ret = []
                for i in range(0,n):
                    ret.append(np.array(data[i]))
                return ret    
        
  
########### CALIBRATE ALIAS COMMANDS ############################

'''
@cal1@
cal1()
Alias for the manualCalibrateDAC1 command
Included in slab.py
'''
def cal1():
    manualCalibrateDAC1()

'''
@cal2@
cal2()
Alias for the adcCalibrate command
Included in slab.py
'''    
def cal2():
    adcCalibrate()
  
'''
@cal3@
cal3()
Alias for the dacCalibrate command
Included in slab.py
'''     
def cal3():
    dacCalibrate()
 
'''
@cal4@
cal4()
Alias for the checkCalibration command
Included in slab.py
'''      
def cal4():
    checkCalibration()   
 
################ PUBLIC COMPLEX DC FUNCTIONS ####################

'''
@dcSweep@
dcSweep(ndac,v1,v2,vi,wt)
Performs a DC Sweep on a DAC and reads all ADCs at each point

Required parameters:
  ndac : DAC to sweep
    v1 : Start voltage
    v2 : End voltage
    
Optional parameters    
    vi : Increment (Defaults to 0.1 V)
    wt : Wait time at each step (Defaults to 0.1 s)
    
Returns a list of vectors
   Vector 0 is the DAC value
   Vectorns 1 onward are ADC values    

Included in slab.py    
'''

def dcSweep(ndac,v1,v2,vi=0.1,wt=0.1):
    # Checks
    if not opened:
        raise SlabEx("Not connected to board")
    if v1 < 0.0:
        raise SlabEx("Voltage cannot be below 0 volts")
    if v1 > vref:
        raise SlabEx("Voltage cannot be over Vref")
    if v2 < 0.0:
        raise SlabEx("Voltage cannot be below 0 volts")
    if v2 > vref:
        raise SlabEx("Voltage cannot be over Vref")        
    if ndac < 1 or ndac > ndacs:
        raise SlabEx("Invalid DAC number")

    checkSciPy()
            
    message(1,"Performing mesurements...")        
            
    # Initialize outputs
    a1 = []
    a2 = []
    a3 = []
    a4 = []   
           
    # Perform the measurements       
    xrange = np.arange(v1,v2,vi)
    for x in xrange:
        message(2,"  DAC at " + str(x) + " V")
        setVoltage(ndac,x)
        wait(wt)
        a1.append(readVoltage(1))
        a2.append(readVoltage(2))
        a3.append(readVoltage(3))
        a4.append(readVoltage(4))
        
    message(1,"Measurement ends")    

    # Return results
    return xrange,np.array(a1),np.array(a2),np.array(a3),np.array(a4)
    
################## PUBLIC PLOTTING FUNCTIONS ####################


'''
Plot two magnitudes using log if needed
Used by the plot11, plot1n and plotnn commands
'''
def plotXY(x,y,label="",logx=False,logy=False):
    if not logx and not logy:
        pl.plot(x,y,label=label)
        return
    if logx and not logy:
        pl.semilogx(x,y,label=label)
        return
    if logy and not logx:
        pl.semilogy(x,y,label=label)
        return
    if logx and logy:
        pl.loglog(x,y,label=label)
        return

'''
@setPlotReturnData@
setPlotReturnData(value)
Configures if plot commands shoud return the plotted data

Optional parameters:
  value : By default is False
Returns nothing 
Included in slab.py  
'''
def setPlotReturnData(value=False):
    global plotReturnData
    plotReturnData = value

'''
@plot11@
plot11(x,y,title,xt,yt,logx,logy)
Plot one input against one output
If x is an empty list [], a sequence number
will be used for the x axis

Required parameters:
  x : Horizontal vector
  y : Vertical vector
  
Optional parameters:
  title : Plot title (Defaults to none)
     xt : Label for x axis (Defaults to none)
     yt : Label for y axis (Defaults to none)
   logx : Use logarithmic x axis (Defaults to False)
   logy : Use logarithmic x axis (Defaults to False)

Returns nothing
Included in slab.py      
'''
def plot11(x,y,title="",xt="",yt="",logx=False,logy=False):

    # Check if SciPy is loaded
    if not scipy:
        cannotPlot(exception=True)
        return
       
    # Generate sequence if x is not provided
    if x == []:
        x = np.arange(0,len(y))
       
    plt.figure(facecolor="white")   # White border
    plotXY(x,y,logx=logx,logy=logy)
    pl.xlabel(xt)
    pl.ylabel(yt)
    pl.title(title)
    pl.grid()
    pl.show()
    pl.close()
    
'''
@plot1n@
plot1n(x,ylist,title,xt,yt,labels,location,logx,logy)
Plot one input against several outputs
If x is an empty list [], a sequence number
will be used for the x axis

Required parameters:
      x : Horizontal vector
  ylist : List of vertical vectors
  
Optional parameters:
    title : Plot title (Defaults to none)
       xt : Label for x axis (Defaults to none)
       yt : Label for y axis (Defaults to none)
   labels : List of legend labels (Defaults to none)
 location : Location for legend (Defaults to 'best')
     logx : Use logarithmic x axis (Defaults to False)
     logy : Use logarithmic x axis (Defaults to False)

Returns nothing
Included in slab.py     
'''
def plot1n(x,ylist,title="",xt="",yt="",labels=[],location='best',logx=False,logy=False):

    # Check if SciPy is loaded
    if not scipy:
        cannotPlot(exception=True)
        return

    # Generate sequence is x is not provided
    if x == []:
        x = np.arange(0,len(ylist[0]))        
        
    plt.figure(facecolor="white")   # White border
    if labels == []:
        for y in ylist:
            plotXY(x,y,logx=logx,logy=logy)
            #pl.plot(x,y)
    else:
        for y,lbl in zip(ylist,labels):
            plotXY(x,y,label=lbl,logx=logx,logy=logy)
            #pl.plot(x,y,label=lbl)
    pl.xlabel(xt)
    pl.ylabel(yt)
    pl.title(title)
    pl.grid()
    if not labels == []:
        pl.legend(loc=location)
    pl.show() 
    pl.close()    
  
'''
@plotnn@
plotnn(xlist,ylist,title,xt,yt,labels,location,logx,logy)
Plot several curves with different inputs and outputs

Required parameters:
  xlist : List of horizontal vector
  ylist : List of vertical vectors
  
Optional parameters:
    title : Plot title (Defaults to none)
       xt : Label for x axis (Defaults to none)
       yt : Label for y axis (Defaults to none)
   labels : List of legend labels (Defaults to none)
 location : Location for legend (Defaults to 'best')
     logx : Use logarithmic x axis (Defaults to False)
     logy : Use logarithmic x axis (Defaults to False)

Returns nothing
Included in slab.py     
'''
def plotnn(xlist,ylist,title="",xt="",yt="",labels=[],location='best',logx=False,logy=False):

    # Check if SciPy is loaded
    if not scipy:
        cannotPlot(exception=True)
        return

    plt.figure(facecolor="white")   # White border
    if labels == []:
        for x,y in zip(xlist,ylist):
            plotXY(x,y,logx=logx,logy=logy)
    else:
        for x,y,lbl in zip(xlist,ylist,labels):
            plotXY(x,y,label=lbl,logx=logx,logy=logy)
    pl.xlabel(xt)
    pl.ylabel(yt)
    pl.title(title)
    pl.grid()
    if not labels == []:
        pl.legend(loc=location)
    pl.show()  
    pl.close()    
  
    
######################### DC SWEEP PLOT ############################

'''
@dcSweepPlot@
dcSweepPlot(ndac,v1,v2,vi,na,wt,returnData)
Plots the results of a DC sweep

Required parameters: 
 ndac : DAC to sweep
   v1 : Initial value (in Volt)
   v2 : End of range (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)  
  na : Number of ADCs to show (defaults to 4)
  wt : Waiting time between steps (defaults to 0.1s)
  returnData : Enable return of plot data (Defaults to False)
  
Returns plot data if enabled (see also setPlotReturnData)
Included in slab.py 
''' 
def dcSweepPlot(ndac,v1,v2,vi=0.1,na=4,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    if not scipy:
        cannotPlot(exception=True)
        return

    # Perform a DC sweep
    res = dcSweep(1,v1,v2,vi,wt)
    
    if na == 1:
        # Plot result
        message(1,"Drawing curve")
        plot11(res[0],res[1],"V(V) Plot","DAC"+str(ndac)+" (V)","ADC1 (V)")
        ret = [res[0],res[1]]
    else:
        ylist=[]
        labels=[]
        ret=[res[0]]
        for i in range(0,na):
            ylist.append(res[i+1])
            ret.append(res[i+1])
            labels.append("ADC"+str(i+1))
        plot1n(res[0],ylist,"DC Sweep Plot","DAC"+str(ndac)+" (V)","ADC(V)",labels)
    
    if plotReturnData or returnData:
        return ret
   
   
######################### REALTIME PLOT ############################   

'''
@realtimePlot@
realtimePlot(nadc,wt,returnData)
Plots ADC data in real time

Optional parameters:
        nadc : Number of ADCs to read (Defaults to 1)
          wt : Wait time between read (Defaults to 0.2s)
           n : Number of points to show (Defaults to All)
  returnData : Returns captured data if true (Defaults to False)
  
Returns a time+nadc list if returnData is true  
Included in slab.py   
'''
def realtimePlot(nadc=1,wt=0.2,n=0,returnData=False):

    nn=int(n)

    # Checks
    if not opened:
        raise SlabEx("Not connected to board")  
    if nadc < 1 or nadc > nadcs:
        raise SlabEx("Invalid number of ADCs")
    
    # Initialize the data arrays    
    vt = []
    va = []
    for i in range(0,nadc):
        va.append([])
        
    message(1,"Entering realtime plot")
    message(1,"Close the graph window to exit")

    #plt.ion()    
    
    fig=plt.figure(facecolor="white")   # White border
    ax=fig.add_subplot(1,1,1)
    pl.xlabel("time (s)")
    pl.ylabel("Value (V)")
    pl.title("Realtime Plot")
    pl.grid()
    
    labels=[]
    for i in range(0,nadc):
        labels.append("ADC"+str(i+1))
        
    toffs=-1.0
    try:    
        while True:
            t = time.time()
            if toffs < 0.0:
                toffs=t
            t=t-toffs    
            vt.append(t)
            
            for i in range(0,nadc):
                value = readVoltage(i+1)
                va[i].append(value)
                
            ax.cla()    
            ax.grid()
            pl.xlabel("time (s)")
            pl.ylabel("Value (V)")
            pl.title("Realtime Plot") 
            
            for i in range(0,nadc):
                if nn:
                    ax.plot(vt[-nn:-1], va[i][-nn:-1], label=labels[i])
                else:
                    ax.plot(vt, va[i], label=labels[i])
                
            if nadc>1:
                pl.legend(loc='lower right')   
            
            fig.canvas.draw()
            plt.pause(wt)
               
    except:
        print
        print "End of realtime measurements"
        print    

    plt.close()

    plot1n(vt,va,"Measurement Plot","time (s)","Value (V)",labels)   

    if plotReturnData or returnData:
        ret = vt
        ret.extend(va)
        return ret 
    

   
################ PUBLIC BASIC TRANSIENT FUNCTIONS ####################    

'''
@setSampleTime@
setSampleTime(st)
Set sample time for time measurements
Resolution on sample time is limited so value set 
can be different of the input value
Check your hardware board limits

Required parameter:
  st : Sample time (float seconds)
  
Returns real sample time set
Included in slab.py   
'''
def setSampleTime(st):
    global sampleTime
    
    # Check
    if st > 100.0:
        raise SlabEx("Sample time too high")
    if st < 0.000005:  
        raise SlabEx("Sample time too low") 
        
    startCommand('R')
    sampleTime = sendFloat(st)
    sendCRC()
    
    checkACK()
    checkCRC()
    
    return sampleTime
 

'''
Check of storage space
Gives exception if there is not enough space
'''
def checkBuffSpace(samples,na,nd=0):
    # Assert
    if not nd == 0:
        raise SlabEx("Digital signals are not supported yet")
        
    # Calculate space    
    space = buff_size - w_points - w_points2
    required = samples * na 
    if space < required:
        raise SlabEx("Not enough buffer space. Only " + str(space) + " samples free")
 
'''
@setTransientStorage@
setTransientStorage(samples,na)
Set storage for samples in transient time measurements
Check your hardware board limits

Required parameters:
  samples : Number of samples to obtain
  
Optional parameters:  
  na : Number of ADC analog signals to record
       (Defaults to 1)
       
Returns nothing
Included in slab.py 

This command has an alias tranStore
'''    
def setTransientStorage(samples,na=1,nd=0):
    if nd != 0:
        raise SlabEx("Digita signals not implented yet")
    
    # Check space
    checkBuffSpace(samples,na,nd)
    
    startCommand('S')
    sendByte(na)
    sendByte(nd)
    sendU16(samples)
    sendCRC()
    
    checkACK()
    checkCRC()
   
'''
@tranStore@
tranStore(samples,na)
Alias for the command setTransientStorage
Included in slab.py 
'''   
def tranStore(samples,na=1,nd=0):
    setTransientStorage(samples,na,nd)
   
'''
@transientAsync@
transientAsync()
Performs an asynchronous transient measurement

Returns a list of vectors
  Vector 0 is time
  Vectors 1 onward are ADC readings
  
Included in slab.py  
See also setSampleTime and setTransientStorage  
'''   
def transientAsync():

    message(1,"Performing transient measurement..." )
   
    startCommand('Y')
    sendCRC()
    
    checkACK()
    
    # Check for overrun or other errors
    code = getByte()
    if code == 1:
        checkCRC()
        raise SlabEx("Sample overrun")
    if code == 3:
        checkCRC()
        raise SlabEx("Halt from board")
    if code != 0: 
        raise SlabEx("Unknown transient response code")
    
    message(1,"Mesurement ends. Receiving data")
    
    na = getByte()
    nd = getByte()
    if nd!=0:
        raise SlabEx("Digital transient is not supported Yet")
    samples = getU16()
    result = []
    vector = []
    for s in range(0,samples):
        vector.append(s*sampleTime)
    if scipy:    
        result.append(np.array(vector))
    else:
        result.append(vector)    
    for i in range(0,na):
        vector = []
        for s in range(0,samples):
            fvalue = dc_cal(getU16()/65536.0,xcal,adcCalData[i])
            fvalue = fvalue * vref
            vector.append(fvalue)
        if scipy:    
            result.append(np.array(vector))
        else:
            result.append(vector)

    checkCRC()    
        
    message(1,"Data received")
        
    return result    
        
'''
@transientTriggered@
transientTriggered(level,mode,timeout)
Performs a triggered transient measurement
Mesuremenst will be centered at the trigger point

Required parameters:
  level : Trigger level (float voltage)
  
Optional parameters:  
   mode : Trigger mode (tmodeRise or tmodeFall)
          (Defaults to tmodeRise)
   timeout : Timeout in integer seconds (Defaults to no timeout)       
   
Returns a list of vectors
  Vector 0 is time
  Vectors 1 onward are ADC readings   
   
Included in slab.py    
See also setSampleTime and setTransientStorage     
''' 
def transientTriggered(level,mode=tmodeRise,timeout=0):
    # Check timeout
    timeout = int(timeout)
    if timeout > 255:
        raise SlabEx("Timeout limited to 255 seconds")
    if timeout < 0:
        raise SlabEx("Timeout cannot be negative")

    # Convert level to uint16 considering calibration
    ratio = voltage2ratio(level)
    cal_ratio = dc_cal(ratio,ycal1,xcal) # Reverse calibration
    counts = ratio2counts(cal_ratio)
        
    message(1,"Performing transient triggered measurement...")
        
    startCommand('G')
    sendU16(counts)
    sendByte(mode)
    sendByte(timeout)
    sendCRC()
    
    # Receive data
    checkACK()
    
    # Check for overrun or other errors
    code = getByte()
    if code == 1:
        checkCRC()
        raise SlabEx("Sample overrun")
    if code == 2:
        checkCRC();
        raise SlabEx("Timeout error")
    if code == 3:
        checkCRC()
        raise SlabEx("Halt from board")
    if code != 0: 
        raise SlabEx("Unknown transient response code")        

    
    message(1,"Mesurement ends. Receiving data")
    
    na = getByte()
    nd = getByte()
    if nd!=0:
        raise SlabEx("Digital transient is not supported Yet")
    samples = getU16()
    result = []
    vector = []
    
    # Determine the trigger sample
    tsample = samples / 2 - 1
    
    for s in range(0,samples):
        vector.append((s - tsample)*sampleTime)
    if scipy:    
        result.append(np.array(vector))
    else:
        result.append(vector)
    for i in range(0,na):
        vector = []
        for s in range(0,samples):
            fvalue = dc_cal(getU16()/65536.0,xcal,adcCalData[i])
            fvalue = fvalue * vref
            vector.append(fvalue)
        if scipy:    
            result.append(np.array(vector))
        else:
            result.append(vector)

    checkCRC()    
        
    message(1,"Data received")
        
    return result          
    
'''
@stepResponse@
stepResponse(v1,v2,t)
Obtains the Step Response for a circuit
  1/5 of measurement time will be before the step
  4/5 of measurement time will be after the step
  
Required parameters:
       v1 : Start voltage
       v2 : End voltage
       
Optional parameters:       
    tinit : Time before start in seconds (defaults to 1 s)
    
Returns a list of vectors
  Vector 0 is time
  Vectors 1 onward are ADC readings   

Included in slab.py   
See also setSampleTime and setTransientStorage       
'''   
def stepResponse(v1,v2,tinit=1.0):
    message(1,"Performing step response...")
   
    setVoltage(1,v1)
    time.sleep(tinit)
    v2cal = dc_cal(v2,dacx,dac1y)  
    counts = voltage2counts(v2)
    
    readADC(1);  # Precharge ADC inputs
    readADC(2);  # and discard the reading
    readADC(3);
    readADC(4);
    
    startCommand('P')
    sendU16(counts)
    sendCRC()
    
    # Receive data
    checkACK()
    
    # Check for overrun or other errors
    code = getByte()
    if code == 1:
        checkCRC()
        raise SlabEx("Sample overrun")
    if code == 3:
        checkCRC()
        raise SlabEx("Halt from board")
    if code != 0: 
        raise SlabEx("Unknown transient response code")           
    
    message(1,"Mesurement ends. Receiving data")
    
    na = getByte()
    nd = getByte()
    if nd!=0:
        raise SlabEx("Digital transient is not supported Yet")
    samples = getU16()
    result = []
    vector = []
    
    # Determine the trigger sample
    tsample = samples / 5
    
    for s in range(0,samples):
        vector.append((s - tsample)*sampleTime)
    if scipy:    
        result.append(np.array(vector))
    else:
        result.append(vector)
    for i in range(0,na):
        vector = []
        for s in range(0,samples):
            fvalue = dc_cal(getU16()/65536.0,xcal,adcCalData[i])
            fvalue = fvalue * vref
            vector.append(fvalue)
        if scipy:    
            result.append(np.array(vector))
        else:
            result.append(vector)
        
    checkCRC()

    setVoltage(1,v1)
    
    message(1,"Data received")
        
    return result      
        
################## PUBLIC AC PLOT FUNCTIONS ####################        

'''
@tranAsyncPlot@
tranAsyncPlot(returnData)
Plots an asynchronous transient measurement

Optional parameter:
  returnData : Enable return of plot data (Defaults to False)

Returns plot data if enabled
  Vector 0 is time
  Vectors 1 onward are ADC readings

Included in slab.py   
See also setSampleTime, setTransientStorage and setPlotReturnData
'''
def tranAsyncPlot(returnData=False):

    if not scipy:
        cannotPlot(exception=True)
        return

    # Perform measurement
    res = transientAsync()
    # Plot result
    message(1,"Drawing curves")
    plt.figure(facecolor="white")   # White border
    for i in range(1,len(res)):
        if (len(res) == 2):
            # Only one plot
            pl.plot(res[0],res[i])
        else:    
            # More than one plot
            pl.plot(res[0],res[i],label=adcNames[i-1])
    pl.xlabel("Time (s)")
    pl.ylabel("Voltage (V)")
    pl.title("Async Transient Plot")
    if (len(res) > 2):
        # More than one plot
        pl.legend(loc='lower right')        
    pl.grid()
    pl.show()
    pl.close()
    
    if plotReturnData or returnData:
        return res    

'''
@tranTriggeredPlot@
tranTriggeredPlot(level,mode,timeout,returnData)
Plots a triggered transient measurement
Mesuremenst will be centered at the trigger point

Required parameters:
  level : Trigger level (float voltage)
  
Optional parameters:  
   mode : Trigger mode (tmodeRise or tmodeFall)
          (Defaultst to tmodeRise)
   timeout : Timeout in integer seconds (Defaults to no timeout)           
   returnData : Enable return of plot data (Defaults to False)
   
Returns plot data if enabled
  Vector 0 is time
  Vectors 1 onward are ADC readings   

Included in slab.py   
See also setSampleTime, setTransientStorage and setPlotReturnData
'''
def tranTriggeredPlot(level,mode=tmodeRise,timeout=0,returnData=False):

    if not scipy:
        cannotPlot(exception=True)
        return

    # Perform measurement
    res = transientTriggered(level,mode,timeout)
    # Plot result
    message(1,"Drawing curves")

    plt.figure(facecolor="white")   # White border
    for i in range(1,len(res)):
        if (len(res) == 2):
            # Only one plot
            pl.plot(res[0],res[i])
        else:    
            # More than one plot
            pl.plot(res[0],res[i],label=adcNames[i-1])
    pl.xlabel("Time (s)")
    pl.ylabel("Voltage (V)")
    pl.title("Transient Triggered Plot")
    if (len(res) > 2):
        # More than one plot
        pl.legend(loc='lower right')        
    pl.grid()
    pl.show()  
    pl.close()
    
    if plotReturnData or returnData:
        return res    

'''
@stepPlot@  
stepPlot(v1,v2,tinit,returnData)  
Plots the Step Response for a circuit
  1/5 of measurement time will be before the step
  4/5 of measurement time will be after the step
  
Required parameters:
  v1 : Start voltage
  v2 : End voltage
       
Optional parameters:       
  tinit : Time before start in seconds (defaults to 1 s)
  returnData : Enable return of plot data (Defaults to False)
    
Returns plot data if enabled (see setPlotReturnData) 
  Vector 0 is time
  Vectors 1 onward are ADC readings   

Included in slab.py   
See also setSampleTime, setTransientStorage and setPlotReturnData
'''
def stepPlot(v1,v2,tinit=1.0,returnData=False):

    if not scipy:
        cannotPlot(exception=True)
        return

    # Perform measurement
    res = stepResponse(v1,v2,tinit)
    # Plot result
    message(1,"Drawing curves")
    plt.figure(facecolor="white")   # White border
    for i in range(1,len(res)):
        if (len(res) == 2):
            # Only one plot
            pl.plot(res[0],res[i])
        else:    
            # More than one plot
            pl.plot(res[0],res[i],label=adcNames[i-1])
    pl.xlabel("Time (s)")
    pl.ylabel("Voltage (V)")
    pl.title("Step Response Plot")
    if (len(res) > 2):
        # More than one plot
        pl.legend(loc='lower right')        
    pl.grid()
    pl.show() 
    pl.close()
    
    if plotReturnData or returnData:
        return res    
 
################## WAVETABLE COMMANDS #################

'''
@loadWavetable@
loadWavetable(list,second=False)
Load one wavetable on the hardware board
Loading a primary wavetable erases the secondary if present

Required parameters:
  list : List of values of the wavetable
         If empty [] the wavetable will be erased
    
Optional parameters:
  second : Load secondary wavetable for DAC2
           (Defaults to false)    

Included in slab.py            
Returns nothing
'''
def loadWavetable(list,second=False): 
    global w_idle,w_idle2,w_points,w_points2

    # Get list size
    size = len(list)
        
    # Checks
    if not opened:
        raise SlabEx("Not connected to board")    
    if size > buff_size :
        raise SlabEx("Wavetable too big")
        
    # Additional check for secondary wavetable
    if second:
        if size > buff_size - w_points:
            raise SlabEx("Not enough space for secondary wavetable")
        
    # Send data
    if not second:
        w_points = size      # Size of main wavetable
        if size > 0:         # Iddle value (Volt) 
            w_idle = list[0]    
        else:
            w_idle = -1        
        w_idle2 = -1         # Eliminate secondary wavetable
        w_points2 = 0
        startCommand('W')    # Start
    else:
        w_points2 = size     # Size of secondary wavetable
        if size > 0:
            w_idle2 = list[0]    # Iddle value (Volt)
        else:
            w_idle2 = -1
        startCommand('w')    # Start
        
    sendU16(size)
    if size > 0:
        for value in list:
            ratio = value/vref
            if not second:
                rCal = dc_cal(ratio,dacx,dac1y) 
            else:
                rCal = dc_cal(ratio,dacx,dac2y)
            counts = ratio2counts(rCal)
            sendU16(counts)
        
    sendCRC()
    
    checkACK()
    checkCRC()    
        
    if not second and size > 0:    
        # Inform on frequency only on main wave
        fmax = 1.0/(w_points * min_sample)
        fmin = 1.0/(w_points * max_sample)
        message(1,str(w_points) + " point wave loaded")
        message(1,"Wave frequency must be between " + "{:.6f}".format(fmin) + " and " + "{:.2f}".format(fmax) + " Hz")
        frequency = 1.0 /(sampleTime * w_points)
        message(1,"Current frequency is " + str(frequency) + " Hz")
        
    # Inform on space
    space = buff_size - w_points - w_points2
    message(1,"Remaining buffer space is " + str(space) + " samples")
 
'''
@waveSquare@
waveSquare(v1,v2,np,returnList,second)
Loads square wavetable omn the hardware board

Required parameters:
  v1 : Start value
  v2 : End value
  np : Number of points for a full wave
    
Optional parameters:    
 returnList : Request a return list (Default False)
     second : Load on secondary table
              (Defaults to false) 
               
If returnList is True, returns the table of loaded values
Included in slab.py 
''' 
def waveSquare(v1,v2,np,returnList=False,second=False):
    # Check
    if not opened:
        raise SlabEx("Not connected to board")
    if np < 4:
        raise SlabEx("Not enough points for wave")
        
    # Create wave
    list = []
    for point in range(0,np):
        if point < np/2.0:
            list.append(v1)
        else:
            list.append(v2)
            
    # Program wave 
    loadWavetable(list,second)
    
    # Return list
    if returnList:
        return list

'''
@wavePulse@
wavePulse(v1,v2,np,n1,returnList,second)
Loads a pulse wavetable on the hardware board

Parameters:
  v1 : Start value
  v2 : End value
  np : Number of points for a full wave 
  n1 : Number of points at v1
           
Optional parameters:    
 returnList : Request a return list (Default False)
     second : Load on secondary table
              (Defaults to false)   
              
If returnList is True, returns the table of loaded values
Included in slab.py 
''' 
def wavePulse(v1,v2,np,n1,returnList=False,second=False):
    # Check
    if not opened:
        raise SlabEx("Not connected to board")
    if np < 4:
        raise SlabEx("Not enough points for wave")
        
    # Create wave
    list = []
    for point in range(0,np):
        if point < n1:
            list.append(v1)
        else:
            list.append(v2)
            
    # Program wave 
    loadWavetable(list,second)    
    
    # Return list
    if returnList:
        return list
    
'''
@waveTriangle@
waveTriangle(v1,v2,np,n1,returnList,second)
Loads a triangle wavetable on the hardware board

Parameters:
   v1 : Minimum value
   v2 : Maximum value
   np : Number of points for a full wave 
           
Optional parameters:    
 returnList : Request a return list (Default False)
     second : Load on secondary table
              (Defaults to false)   
              
If returnList is True, returns the table of loaded values
Included in slab.py 
'''
def waveTriangle(v1,v2,np,returnList=False,second=False):
    # Check
    if not opened:
        raise SlabEx("Not connected to board")
    if np < 4:
        raise SlabEx("Not enough points for wave")

    # Create wave
    list = []
    for point in range(0,np):
        point = (point + np//4) % np
        if point < np/2.0:
            value = v1 + 2.0*(v2-v1)*point/np
        else:
            value = v1 + 2.0*(v2-v1)*(np - point)/np
        list.append(value)
        
    # Program wave 
    loadWavetable(list,second)  

    # Return list
    if returnList:
        return list
    
'''
@waveSawtooth@
waveSawtooth(v1,v2,np,returnList,second)
Loads a sawtooth wavetable on the hardware board

Parameters:
    v1 : Start value
    v2 : End value
    np : Number of points for a full wave 
           
Optional parameters:    
 returnList : Request a return list (Default False)
     second : Load on secondary table
              (Defaults to false)     
   
If returnList is True, returns the table of loaded values
Included in slab.py 
'''
def waveSawtooth(v1,v2,np,returnList=False,second=False):
    # Check
    if not opened:
        raise SlabEx("Not connected to board")
    if np < 4:
        raise SlabEx("Not enough points for wave")
        
    # Create wave
    list = []
    for point in range(0,np):
        value = v1*1.0 + (v2*1.0-v1*1.0)*point/np
        list.append(value)
        
    # Program wave 
    loadWavetable(list,second) 

    # Return list
    if returnList:
        return list   

'''
@waveSine@
waveSine(v1,v2,np,phase,returnList,second)

Generates a sine wavetable
Parameters:
  v1 : Minimum value
  v2 : Maximum value
  np : Number of points for a full wave 
           
Optional parameters:    
      phase : Phase of the signal (deg) (Defaults to 0)
 returnList : Request a return list (Default False)
     second : Load on secondary table
              (Defaults to false)     
   
If returnList is True, returns the table of loaded values
Included in slab.py 
'''
def waveSine(v1,v2,np,phase=0.0,returnList=False,second=False):
    # Check
    if not opened:
        raise SlabEx("Not connected to board")
    if np < 4:
        raise SlabEx("Not enough points for wave")

    # Create wave
    phase = phase*math.pi/180.0
    list = []
    mean = (v1 + v2)/2.0
    amplitude = (v2 - v1)/2.0
    for point in range(0,np):
        value = mean + amplitude*math.sin(2.0*math.pi*point/np+phase)
        list.append(value)
        
    # Program wave 
    loadWavetable(list,second)  

    # Return list
    if returnList:
        return list     
 
'''
@waveCosine@
waveCosine(v1,v2,np,returnList,second)

Generates a cosine wavetable
Parameters:
  v1 : Minimum value
  v2 : Maximum value
  np : Number of points for a full wave 
           
Optional parameters:    
       phase : Phase of the signal (deg) (Defaults to 0)
  returnList : Request a return list (Default False)
      second : Load on secondary table
               (Defaults to false)     
   
If returnList is True, returns the table of loaded values
Included in slab.py 
'''
def waveCosine(v1,v2,np,phase=0.0,returnList=False,second=False):
    # Check
    if not opened:
        raise SlabEx("Not connected to board")
    if np < 4:
        raise SlabEx("Not enough points for wave")

    # Create wave
    phase = phase*math.pi/180.0
    list = []
    mean = (v1 + v2)/2.0
    amplitude = (v2 - v1)/2.0
    for point in range(0,np):
        value = mean + amplitude*math.cos(2.0*math.pi*point/np+phase)
        list.append(value)
        
    # Program wave 
    loadWavetable(list,second)  

    # Return list
    if returnList:
        return list  
        
'''
@waveNoise@
waveNoise(vm,vstd,n,returnList,second)

Generates a noise wavetable
Based on a normal distribution
Samples are truncated between 0 and Vref

Parameters:
    vm : Mean value
  vstd : Standard deviation
     n : Number of points
           
Optional parameters:    
   returnList : Request a return list (Default False)
       second : Load on secondary table
                (Defaults to false)     
   
If returnList is True, returns the table of loaded values
Included in slab.py 
'''
def waveNoise(vm,vstd,n,returnList=False,second=False):
    # Check
    if not opened:
        raise SlabEx("Not connected to board")
    if n < 4:
        raise SlabEx("Not enough points for wave")

    # Create wave
    list = np.random.normal(loc=vm,scale=vstd,size=n)
    for i in range(0,n):
        if list[i] > vref:
            list[i] = vref
        if list[i] < 0.0:
            list[i] = 0
        
    # Program wave 
    loadWavetable(list,second)  

    # Return list
    if returnList:
        return list          
 
'''
@waveRandom@
waveRandom(v1,v2,n,returnList,second)

Generates a random wavetable
Based on a uniform distribution
Samples will be random values between v1 and v2

Parameters:
   v1 : Minimum voltage
   v2 : Maximum voltage
    n : Number of points
           
Optional parameters:    
   returnList : Request a return list (Default False)
       second : Load on secondary table
                (Defaults to false)     
   
If returnList is True, returns the table of loaded values
Included in slab.py 
'''
def waveRandom(v1,v2,n,returnList=False,second=False):
    # Check
    if not opened:
        raise SlabEx("Not connected to board")
    if n < 4:
        raise SlabEx("Not enough points for wave")
    if v1 >= v2 :
        raise SlabEx("v1 must be lower than v2")

    # Create wave
    list = v1 + (v2-v1)*np.random.random(size=n)
        
    # Program wave 
    loadWavetable(list,second)  

    # Return list
    if returnList:
        return list   
 
'''
@setWaveFrequency@
setWaveFrequency(freq)
Set wave frequency by changing sample frequency 

Required parameters:
   freq : Wave frequency in Hz
   
Return sampleTime set
Included in slab.py 
'''   
def setWaveFrequency(freq):
    # Checks
    if freq <= 0.0:
        raise SlabEx("Frequency cannot be negative or zero")
    if w_idle == -1:
        raise SlabEx("No wave loaded")
    # Calculate sample time
    st = 1.0/(w_points * freq)
    if st < min_sample:
        raise SlabEx("Frequency too high")
    if st > max_sample:
        raise SlabEx("Frequency too low")
    # Change sample time
    st = setSampleTime(st)
    frequency = 1/(st * w_points)
    message(1,"Sample time set to " +str(st) + " s")
    message(1,"Wave frequency set to " +str(frequency) + " Hz")
    return st
    
    
 
################## WAVE RESPONSE COMMANDS ################# 
 
'''
@waveResponse@
waveResponse(npre,tinit,dual)
Obtain the response of a circuit against a wave

Measurement sequence:
  1) Set DAC1 to first wave sample during tinit
  2) Send npre waves to DAC1
  3) Start measurement as set on setTransientStorage
     During this time wave continues to be generated

Optional parameters:  
  npre : Number of waves before measurement (default to zero)
 tinit : Time iddle before first wave (default to zero)
  dual : Use dual DAC generation (defaults to False)
 
Returns a list of vectors:
  Vector 0 is time
  Vectors 1 onward are ADC readings          
      
Included in slab.py       
See also setWaveFrequency and setTransientStorage
''' 
def waveResponse(npre = 0,tinit = 1.0,dual=False):
    # Checks
    if not opened:
        raise SlabEx("Not connected to board")  
    if npre < 0:
        raise SlabEx("Invalid number of waves")
    if w_idle < 0:
        raise SlabEx("Wavetable not loaded")
    if dual and w_idle2 < 0:
        raise SlabEx("Secondary wavetable not loaded")

    message(1,"Performing wave measurement...")
        
    # Idle start
    if tinit > 0.0:
        setVoltage(1,w_idle)
        if dual:
            setVoltage(2,w_idle2)
        time.sleep(tinit)
      
    # Send command
    if not dual:
        startCommand('V')
    else:
        startCommand('v')
    sendU16(npre)
    sendCRC()
    
    checkACK()
    
    # Check for overrun or other errors
    code = getByte()
    if code == 1:
        checkCRC()
        raise SlabEx("Sample overrun")
    if code == 3:
        checkCRC()
        raise SlabEx("Halt from board")
    if code != 0: 
        raise SlabEx("Unknown transient response code")          
        
    message(1,"Mesurement ends. Receiving data")    
        
    na = getByte()
    nd = getByte()
    if nd!=0:
        raise SlabEx("Digital transient is not supported Yet")
    samples = getU16()
    result = []
    vector = []
    for s in range(0,samples):
        vector.append(s*sampleTime)
    if scipy:    
        result.append(np.array(vector))
    else:
        result.append(vector)
    for i in range(0,na):
        vector = []
        for s in range(0,samples):
            fvalue = dc_cal(getU16()/65536.0,xcal,adcCalData[i])
            fvalue = fvalue * vref
            vector.append(fvalue)
        if scipy:    
            result.append(np.array(vector)) 
        else:
            result.append(vector)
        
    checkCRC()    

    # Return to iddle
    setVoltage(1,w_idle)  
    
    message(1,"Data received")
        
    return result    
 
'''
@singleWaveResponse@
waveResponse(channel,npre,tinit)
Obtain the response of a circuit against a wave
Response is obtained only on the selected channel
regardless of the setting on setTransientStorage

Measurement sequence:
  1) Set DAC1 to first wave sample during tinit
  2) Send npre waves to DAC1
  3) Start measurement as set on setTransientStorage
     During this time wave continues to be generated

Optional parameters: 
 channel : ADC channel to read (default to 1)
    npre : Number of waves before measurement (default to zero)
   tinit : Time iddle before first wave (default to zero)
 
Returns a list of two:
  Vector 0 is time
  Vectors 1 is ADC readings          
      
Included in slab.py       
See also setWaveFrequency and setTransientStorage
''' 
def singleWaveResponse(channel = 1,npre = 0,tinit = 1.0):

    # Checks
    if not opened:
        raise SlabEx("Not connected to board")  
    if npre < 0:
        raise SlabEx("Invalid number of waves")
    if channel < 1 or channel > 4:
        raise SlabEx("Invalid channel number")
    if w_idle < 0:
        raise SlabEx("Wavetable not loaded")

    message(1,"Performing wave measurement at ADC " + str(channel) + " ...")
            
    # Idle start
    if tinit > 0.0:
        setVoltage(1,w_idle)
        time.sleep(tinit)
      
    # Send command
    startCommand('X')
    sendByte(channel)
    sendU16(npre)
    sendCRC()
    
    checkACK()
    
    # Check for overrun or other errors
    code = getByte()
    if code == 1:
        checkCRC()
        raise SlabEx("Sample overrun")
    if code == 3:
        checkCRC()
        raise SlabEx("Halt from board")
    if code != 0: 
        raise SlabEx("Unknown transient response code")          
        
    message(1,"Mesurement ends. Receiving data")    
        
    na = getByte()
    nd = getByte()
    if nd!=0:
        raise SlabEx("Digital transient is not supported Yet")
    if na!=1:
        raise SlabEx("Internal Error: Only one ADC should be read")    
                
    samples = getU16()
    result = []
    vector = []
    for s in range(0,samples):
        vector.append(s*sampleTime)
    if scipy:    
        result.append(np.array(vector))
    else:
        result.append(vector)
    
    vector = []
    for s in range(0,samples):
        fvalue = dc_cal(getU16()/65536.0,xcal,adcCalData[channel-1])
        fvalue = fvalue * vref
        vector.append(fvalue)
    if scipy:    
        result.append(np.array(vector)) 
    else:
        result.append(vector)
        
    checkCRC()    

    # Return to iddle
    setVoltage(1,w_idle)  
    
    message(1,"Data received")
        
    return result  
 
'''
@wavePlay@
wavePlay(n,tinit,dual)
Generates wave withou measuring

Generation sequence:
  1) Set DAC1 to first wave sample during tinit
  2) Send n waves to DAC1

Optional parameters:  
     n : Number of waves to send (default to one)
           Zero means infinite (Use HALT to end)
 tinit : Time iddle before first wave (default to zero)
  dual : Use dual DAC generation (defaults to False)

Returns nothing  
Included in slab.py 
      
See also setWaveFrequency
''' 
def wavePlay(n = 1,tinit = 1.0,dual=False):
    # Checks
    if not opened:
        raise SlabEx("Not connected to board")  
    if n < 0:
        raise SlabEx("Invalid number of waves")
    if w_idle < 0:
        raise SlabEx("Wavetable not loaded")
    if dual and w_idle2 < 0:
        raise SlabEx("Secondary wavetable not loaded")

    message(1,"Sending wave...")
        
    # Idle start
    if tinit > 0.0:
        setVoltage(1,w_idle)
        if dual:
            setVoltage(2,w_idle2)
        time.sleep(tinit)
      
    # Send command
    if not dual:
        startCommand('Q')
    else:
        startCommand('q')
    sendU16(n)
    sendCRC()
    
    checkACK()
    
    # Check for overrun or other errors
    code = getByte()
    if code == 1:
        checkCRC()
        raise SlabEx("Sample overrun")     
    if code == 3:
        checkCRC()
        raise SlabEx("Halt from board")
    if code != 0: 
        raise SlabEx("Unknown transient response code")          
        
    message(1,"Wave play ends")    
            
    checkCRC()    

    # Return to iddle
    setVoltage(1,w_idle)  
  
 
'''
@wavePlot@
wavePlot(npre,tinit,dual,returnData)
Plot the response of a circuit against a wave

Measurement sequence:
  1) Set DAC1 to first wave sample during tinit
  2) Send npre waves to DAC1
  3) Start measurement as set on setTransientStorage
     During this time wave continues to be generated

Optional parameters:  
 npre : Number of waves before measurement (default to zero)
 tinit : Time iddle before first wave (default to zero)
 dual : Generate waves on both dacs (defaults to False)
 returnData : Enables return of plot data (defaults to False)
 
Returns plot data if enabled
  Vector 0 is time
  Vectors 1 onward are ADC readings          
      
Included in slab.py       
See also setWaveFrequency, setTransientStorage and setPlotReturnData
'''     
def wavePlot(n = 0,tinit = 1.0,dual=False,returnData=False):

    if not scipy:
        cannotPlot(exception=True)
        return

    # Perform measurement
    res = waveResponse(n,tinit,dual)
    
    # Plot result
    message(1,"Drawing curves")
    plt.figure(facecolor="white")   # White border
    for i in range(1,len(res)):
        if (len(res) == 2):
            # Only one plot
            pl.plot(res[0],res[i])
        else:    
            # More than one plot
            pl.plot(res[0],res[i],label=adcNames[i-1])
    pl.xlabel("Time (s)")
    pl.ylabel("Voltage (V)")
    pl.title("Wave Response Plot")
    if (len(res) > 2):
        # More than one plot
        pl.legend(loc='best')        
    pl.grid()
    pl.show() 
    pl.close()
    
    if plotReturnData or returnData:
        return res           
        
'''
@singleWavePlot@
singleWavePlot(channel,npre,tinit,returnData)
Plot the response of a circuit against a wave
Response is obtained only on the selected channel
regardless of the setting on setTransientStorage

Measurement sequence:
  1) Set DAC1 to first wave sample during tinit
  2) Send npre waves to DAC1
  3) Start measurement as set on setTransientStorage
     During this time wave continues to be generated

Optional parameters:  
 channel : ADC channel to use (defaults to 1)
 npre : Number of waves before measurement (default to zero)
 tinit : Time iddle before first wave (default to zero)
 returnData : Enables return of plot data (defaults to False)
 
Returns plot data if enabled 
  Vector 0 is time
  Vectors 1 onward are ADC readings          
      
Included in slab.py       
See also setWaveFrequency, setTransientStorage and setPlotReturnData
'''     
def singleWavePlot(channel=1,n=0,tinit = 1.0,returnData=False):

    if not scipy:
        cannotPlot(exception=True)
        return

    # Perform measurement
    res = singleWaveResponse(channel,n,tinit)
    
    # Plot result
    message(1,"Drawing curve")
    plt.figure(facecolor="white")   # White border
    pl.plot(res[0],res[1])
    pl.xlabel("Time (s)")
    pl.ylabel("Voltage (V)")
    pl.title("Single Wave Response Plot")      
    pl.grid()
    pl.show() 
    pl.close()
    
    if plotReturnData or returnData:
        return res              
     
################## CALCULATIONS WITH VECTORS ###################

'''
@highPeak@
highPeak(vector)
Returns the maximum of a vector
Included in slab.py 
'''
def highPeak(vector):
    value = max(vector)
    return value
    
'''
@lowPeak@
lowPeak(vector)
Returns the minimum of a vector
Included in slab.py 
'''   
def lowPeak(vector):
    value = min(vector)    
    return value

'''
@peak2peak@
peak2peak(vector)
Returns the maximum to minimum difference of a vector
Included in slab.py 
'''     
def peak2peak(vector):
    value = max(vector)-min(vector)
    return value
    
'''
@mean@
mean(vector)
Returns the mean value of a vector
Included in slab.py 
'''     
if scipy:   
    def mean(vector):
        return np.mean(vector)    
    
'''
@halfRange@
halfRange(vector)
Returns the average between maximum and minimum of a vector
Included in slab.py 
'''  
def halfRange(vector):  
    return (max(vector)+min(vector))/2.0
    
'''
@rms@
rms(vector)
Returns the RMS value of a vector
Included in slab.py 
''' 
if scipy:   
    def rms(vector):
        return np.sqrt(np.mean(vector*vector))
    
'''
@std@
std(vector)
Returns the standard deviation of a vector
Included in slab.py 
''' 
if scipy:   
    def std(vector):
        return np.std(vector)
   
  
'''
@softReset@
softReset()
Generates a soft reset on the hardware board
Board state is set to reset condition
Returns nothing
Included in slab.py 
'''   
def softReset():
    global sampleTime
    global w_idle,w_points,w_idle2,w_points2

    # Send Command
    startCommand('E')
    sendCRC()
    checkACK()
    checkCRC()
    
    # Syncronize state
    sampleTime = 0.001  # Default sample time of 1ms
    w_idle = -1         # No wave loaded
    w_points = 0 
    w_idle2 = -1        # No secondary table loaded
    w_points2 = 0
    dcroundings = 10    # Default of 10 readings on DC
    
    # Generate message
    message(1,"Hardware board at reset state")
   
################## DC DIGITAL IO ##############################

'''
@dioMode@
dioMode(line,mode)
Configures a digital I/O line mode

Possible modes are:
      mInput : Normal input mode
     mPullUp : Input with Pull Up
   mPullDown : Input with Pull Down
     mOutput : Output Push Pull
  mOpenDrain : Output with Open Drain
  
Modes use the slab namespace

Required parameter:
  line : Line to configure
  
Optional parameter:
  mode : Mode to configure (Defaults to mInput)

Returns nothing  
Included in slab.py 
'''
def dioMode(line,mode=mInput):
    if not opened:
        raise SlabEx("Not connected to board")
    if line < 1 or line > ndio:
        raise SlabEx("Invalid digital I/O line")
    startCommand('H')
    sendByte(line)
    sendByte(mode)
    sendCRC()
    checkACK()
    checkCRC()
    
'''
@dioWrite@
dioWrite(line,value)
Writes on a digital I/O line mode

Required parameters:
   line : Line to write
  value : Value to write (True of False)

Returns nothing 
Included in slab.py  
'''
def dioWrite(line,value):
    if not opened:
        raise SlabEx("Not connected to board")
    if line < 1 or line > ndio:
        raise SlabEx("Invalid digital I/O line")
    startCommand('J')
    sendByte(line)
    if value:
        sendByte(1)
    else:
        sendByte(0)
    sendCRC()
    checkACK()
    checkCRC()    
   
'''
@dioRead@
dioRead(line)
Reads a digital I/O line mode

Required parameter:
   line : Line to read

Returns state (True of False)
Included in slab.py   
'''
def dioRead(line):
    if not opened:
        raise SlabEx("Not connected to board")
    if line < 1 or line > ndio:
        raise SlabEx("Invalid digital I/O line")
    startCommand('K')
    sendByte(line)
    sendCRC()
    checkACK()
    value = getByte()
    checkCRC()    
    if value:
        return True
    else:
        return False
    
################## CODE EXECUTED AT IMPORT ####################
 
# Remove specific warnings if scipy was loaded 
if scipy:
    warnings.filterwarnings("ignore",".*GUI is implemented.*")
 
# Show version information upon load
message(1,"SLab Module")
message(1,"Version "+str(version_major)+"."+str(version_minor)+" ("+version_date+")")
    
# Indicate if we are running in script or interactive mode    
if hasattr(sys, 'ps1'):
    interactive = True
    message(1,"Running interactively")
else:
    message(1,"Running from script")
    interactive = False
   
# Message if we are in Linxu
if linux:
    message(2,"")
    message(2,"System is Linux")

# Give message if SciPy modules could not be loaded   
if not scipy:
    message(1,"")
    message(1,"Cannot load SciPy modules")
    message(1,"Functionality will be reduced")
    
message(1,"")    
    
    
    
