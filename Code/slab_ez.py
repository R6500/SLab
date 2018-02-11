'''
EZ submodule for the SLab project
It requires and imports slab.py

This module eases the use of the SLab system
It connect with the board when importing the module

You can use the functions without namespace by importing as:

    from slab_ez import *

History:

Version 1.0 : First version (12/5/2017)

'''

import slab
import slab_dc as dc

# Version information
version_major = 1
version_minor = 0
version_date  = "12/5/2017"

###################### INFO FOR THE HELP FILE ##########################

'''
@ez@
EZ Submodule 

Commands common to slab.py:
   help
   readVoltage
   setVoltage
   dcPrint
   zero
   
EZ command topics: 
   liveVoltage
   sweepPlot
   ioCurve
   bridgeCurve
   sineResponse
   triangleResponse
   squareResponse
   sineBridgeResponse

'''

################ Commands common to slab.py ###########################

def help(topic="ez"):
    slab.help(topic)

def readVoltage(ch1,ch2=0):
    return slab.readVoltage(ch1,ch2)

def setVoltage(channel,value):
    slab.setVoltage(channel,value)

def dcPrint():
    slab.dcPrint()
    
def zero():
    slab.zero()
    slab.message(1,"DACs set to zero");
    
def connect():
    slab.connect()
 
    
################ Commands simmplified from slab.py ####################

'''
@liveVoltage@
liveVoltage()
Shows live ADC voltage values
Use CRL+C to exit
Included in slab_ez.py
'''
def liveVoltage():
    slab.message(1,"User CTRL+C to exit")
    slab.dcLive()
    
'''
@sweepPlot@
sweepPlot(v1=0.0,v2=3.0,vi=0.1)
Plots ADC values for a sweep of DAC1 values

Optional parameters:
  v1 : Sweep start (Defaults to 0V)
  v2 : Sweep end (Defaults to 3V)
  vi : Sweep increment (Defaults to 0.1V)
'''  
def sweepPlot(v1=0.0,v2=3.0,vi=0.1):
    slab.dcSweepPlot(1,v1,v2,vi)
    
'''
@sineResponse@
sineResponse(vmin,vmax,freq)
Shows the response against a sine wave
DAC 1 and ADC 1 at input
ADC 2, 3 and 4 as outputs

Optional parameters:
  vmin : Wave minimum (Defaults to 1V)
  vmax : Wave maximum (Defaults to 2V)
  freq : Wave frequency (<150Hz)
         Defaults to 100 Hz

Included in slab_ez.py
'''    

def sineResponse(vmin=1,vmax=2,freq=100):
    slab.waveSine(vmin,vmax,100)
    slab.setWaveFrequency(freq)
    slab.tranStore(500,4)
    slab.wavePlot()
    
'''
@triangleResponse@
triangleResponse(vmin,vmax,freq)
Shows the response against a triangular wave
DAC 1 and ADC 1 at input
ADC 2, 3 and 4 as outputs

Optional parameters:
  vmin : Wave minimum (Defaults to 1V)
  vmax : Wave maximum (Defaults to 2V)
  freq : Wave frequency (<150Hz)
         Defaults to 100 Hz

Included in slab_ez.py
'''    

def triangleResponse(vmin=1,vmax=2,freq=100):
    slab.waveTriangle(vmin,vmax,100)
    slab.setWaveFrequency(freq)
    slab.tranStore(500,4)
    slab.wavePlot()    
    
'''
@squareResponse@
squareResponse(v1,v2,freq)
Shows the response against a square wave
DAC 1 and ADC 1 at input
ADC 2, 3 and 4 as outputs

Optional parameters:
    v1 : Start value (Defaults to 1V)
    v2 : Value after step (Defaults to 2V)
  freq : Wave frequency (<150Hz)
         Defaults to 100 Hz

Included in slab_ez.py
'''    

def squareResponse(v1=1,v2=2,freq=100):
    slab.waveSquare(v1,v2,100)
    slab.setWaveFrequency(freq)
    slab.tranStore(500,4)
    slab.wavePlot()    
    
'''
@sineBridgeResponse@
sineBridgeResponse(vmax,freq)
Shows the response against a sine wave
Input between DAC1+ADC1 and DAC2+ADC2
Output between ADC3 and ADC4

Optional parameters:
  vmax : Wave maximum (Defaults to 3V)
  freq : Wave frequency (<150Hz)
         Defaults to 100 Hz

Included in slab_ez.py
'''    

def sineBridgeResponse(vmax=3.0,freq=100.0):
    base = 3.1 - vmax
    slab.waveSine(base,base+vmax,100)
    slab.setWaveFrequency(freq)
    slab.waveSine(base+vmax,base,100,second=True)
    slab.tranStore(500,4)
    t,a1,a2,a3,a4 = slab.waveResponse(dual=True)
    vi=a1-a2
    vo=a3-a4
    slab.plot1n(t,[vi,vo],"Sine Bridge Response","time (s)","Vi,Vo (V)",["Vi","Vo"])
    
'''
@trendPlot@
trendPlot()
Shows all ADCs evolution with time

Optional parameters:
  n : Number of ADCs to show (defaults to 4)

Included in slab_ez.py
'''        
def trendPlot(n=4):
    slab.realtimePlot(n)
    
############### Commands simplified from dc.py #######################
   
'''
@ioCurve@
ioCurve()
Draws an input to output DC curve
Input is between DAC1+ADC1 and GND with 0V to 3V range
Output is between ADC2 and GND
Included in slab_ez.py
'''   
def ioCurve():
    slab.message(1,"Input between DAC1+ADC1 and GND")
    slab.message(1,"Output between ADC2 and GND")
    
    # Perform a DC sweep
    x,y1,y2,y3,y4 = slab.dcSweep(1,0.0,3.0,0.1)
    
    # Plot result
    slab.message(1,"Drawing curve")
    slab.plot11(y1,y2,"V(V) Plot","Input (V)","Output(V)")

    
'''
@bridgeCurve@
bridgeCurve()
Draws an input to output dc curve in bridge mode
Input is between DAC 1 and DAC 2 with a +/-3V range
and read between ADC 1 and ADC 2
Output is read between ADC 3 and 4
Included in slab_ez.py
'''    
def bridgeCurve():
    slab.message(1,"Input between DAC1+ADC1 and DAC2+ADC2")
    slab.message(1,"Output between ADC3 and ADC4")
    dc.curveVVbridge(3.1,3.1,0.1,0.1)
 
################## CODE EXECUTED AT IMPORT #################### 
    
# Show version information upon load
slab.message(1,"SLab EZ Submodule")
slab.message(1,"Version "+str(version_major)+"."+str(version_minor)+" ("+version_date+")")
slab.message(1,"")
slab.message(1,"Connecting with the board")
slab.message(1,"")
slab.connect()


     