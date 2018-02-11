'''
SLab
board_check.py
Checks a connected board

You shall make the following connections on the board

For two DAC boards

   DAC1-----ADC1+ADC3+ADC4
   DAC2-----ADC2

For three DAC boards

   DAC1----ADC1+ADC4
   DAC2----ADC2
   DAC3----ADC3
   
'''

import numpy as np                # Numpy for math calculations
import pylab as pl                # Pylab and Mathplotlib for plotting

import slab as sl

import matplotlib.pyplot as plt

# Open serial communication with autodetection of COM port
sl.connect() 
        
print 
print "This script checks the low level commands that the"
print "SLab module can issue to the hardware board"
print "A functional compliant hardware board should give"
print "Ok results in all checks"
print
print "In order to continue you must set the following connections:"
print "    Each DAC connected to the ADC with the same number"
print "    The rest of ADCs connected to DAC 1"
print
sl.pause()

print
print "[ ] Command M checked if board is connected"        
        
# Show capabilities
sl.printBoardInfo()   

print "[ ] Command F checked if board name is ok"  
print "[ ] Command I checked if board information is ok" 
print "[ ] Command L checked if pin list is ok" 
print  
        
print "[ ] Commands A and D ok if next four curves are"
print "    all lines with equal X and Y axis values"
print        
print "Performing measurements..."        
  
             
# Obtain curves 
a1 = []
a2 = []
a3 = []
a4 = []
xrange = np.arange(0.0,1.1,0.1)
for x in xrange:
    sl.writeDAC(1,x)
    sl.writeDAC(2,x)
    if sl.ndacs>=3:
        sl.writeDAC3(x)
    sl.wait(0.1)
    a1.append(sl.readADC(1))
    a2.append(sl.readADC(2))
    a3.append(sl.readADC(3))
    a4.append(sl.readADC(4))
    
# Plot
print "Drawing curves"

plt.figure(facecolor="white")   # White border
pl.plot(xrange,a1,label="ADC1(DAC1)")
pl.plot(xrange,a2,label="ADC2(DAC2)")
if sl.ndacs<3:
    pl.plot(xrange,a3,label="ADC3(DAC1)") 
else:
    pl.plot(xrange,a3,label="ADC3(DAC3)")  
pl.plot(xrange,a4,label="ADC4(DAC1)") 

pl.legend(loc='lower right')         
pl.title("ADC(DAC) Test Curves")
pl.xlabel("DAC Ratiometric value")
pl.ylabel("ADC Ratiometric value")   
pl.grid()    
pl.show()    
 
 
 
sl.setSampleTime(0.002)
print "Sample time set to 2ms"
sl.setTransientStorage(200,1)
print "Transient storage set to 200 points"
sl.setVoltage(1,1.0)

print
print "[ ] Commands R, S and Y checked in next curve if:"
print "         Voltage is about 1V"
print "         Maximum time is 0.4s"
print "         Resolution is 2ms"
print

sl.tranAsyncPlot() 

print "For the next test you need to take and put ADC1 cable"
print "during the transient triggered test"
print "Sometimes you should connect it to GND and Vdd in sequence"
print "After the curve is drawn, reconnect ADC1 to DAC1"
print
print "[ ] Command G checked if you get a curve"
print "    with transition at time zero"
print
sl.writeDAC(1,1.0)
sl.tranTriggeredPlot(1.5,sl.tmodeFall)

print
print " [ ] Command P checked if you get a step in next curve"
print
sl.stepPlot(0.0,1.0)

print
print " [ ] Commands W and V checked if you get:"
print "         Two periods of a sine wave on ADC1"
print

sl.waveSine(1.0,2.0,100)
sl.wavePlot(1,tinit=0.1)

print
print " [ ] Command X checked if you also get:"
print "         Two periods of a sine wave on ADC1"
print

sl.singleWavePlot()

print
print " [ ] Commands w and v checked if you get:"
print "         Two periods of a sine wave on ADC1"
print "         One period of a triangle wave on ADC2"
print

sl.waveTriangle(1.0,2.0,200,second=True)
sl.setTransientStorage(200,2)
sl.wavePlot(1,tinit=0.1,dual=True)



#print
#print " [ ] DAC to ADC delay calibrated if phase is flat"
#print
#sl.bodeResponse(1.0,2.0,10.0,1000.0,10,maxfs=10000.0)



# Close serial communication
print  "Closing connection"

print
print " End of test"
print

sl.disconnect()



    
