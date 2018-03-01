'''
slabTest.py

Test the SLab functionalities

History:
  01/03/2018 : First version
'''

from __future__ import print_function

import slab
import numpy as np

VERSION = '1/3/2018'

'''
Script configuration
'''
pause_after_connect = False   # By default we don't pause the test
pause_after_info = False
check_dcPrint = False         # By default we don't check dcPrint

'''
Helper functions
'''

def compare(a,b):
    high = a*1.05
    low  = a*0.95
    if a >= 0.0:
        if b > high or b < low:
            return False
        else:
            return True
    else:
        if b < high or b > low:
            return False
        else:
            return True    

def zeroCompare(a,margin):
    if a>margin or a<-margin:
        return False
    else:
        return True    

def isVectorConstant(vector,value):
    if not compare(slab.lowPeak(vector),value):
        return False
    if not compare(slab.highPeak(vector),value):
        return False  
    return True    
    
def isVectorZero(vector,value):
    if not zeroCompare(slab.lowPeak(vector),value):
        return False
    if not zeroCompare(slab.highPeak(vector),value):
        return False  
    return True       
        
'''
Initial messages
'''
print()
print('SLab test suite (version: '+VERSION+')')
print()

'''
Commands without connection to the board
'''

print("Test of commands that don't require the board to be connected")
print()

# Commands: save, load
print('Checking file commands')
data1=[1,2,3]
slab.save('slabTest.dat',data1)
data2=slab.load('slabTest.dat')
if data1 != data2:
    raise slab.SlabEx("Read data don't match saved data")
print('pass')
print()

# Commands: highPeak, lowPeak, peak2peak, halfRange, mean, rms, std
data1=np.arange(0,6,0.01)
data2=0.5+np.sin(data1)
data3=np.arange(0,3,0.01)
data4=0.2+np.cos(data3)
print('Vector utility commands')
if not compare(slab.highPeak(data2),1.5):
    raise slab.SlabEx("highPeak fails")
print('  highPeak pass')
if not compare(slab.lowPeak(data2),-0.5):
    raise slab.SlabEx("lowPeak fails")
print('  lowPeak pass')
if not compare(slab.peak2peak(data2),2.0):
    raise slab.SlabEx("peak2peak fails")
print('  peak2peak pass')
if not compare(slab.halfRange(data2),0.5):
    raise slab.SlabEx("halfRange fails")
print('  halfRange pass')
if not compare(slab.mean(data2),0.5):
    raise slab.SlabEx("mean fails")
print('  mean pass')
if not compare(slab.rms(data2),0.8827):
    raise slab.SlabEx("rms fails")
print('  rms pass')
if not compare(slab.std(data2),0.707):
    raise slab.SlabEx("std fails")
print('  std pass')
print()

# Command: plotnn
print('Plot commands')
print('You should see a plot with two curves')
print('Close the window to continue')
slab.plotnn([data1,data3],[data2,data4],"Two curve plot","Angle (rad)","Value",["Sin","Cos"])
print();

'''
Connection to the board
'''

slab.connect()

print('You should be now connected to the board')
print('If you had performed the calibration, it should load')
if pause_after_connect:
    slab.pause('(Press return)')
print()

slab.printBoardInfo()
print()
print('You should see information about the board')
print('Now connect DAC1 to ADC1,3,4 and DAC2 to ADC2')
if pause_after_info:
    slab.pause('(Press return)')
print()
   
#DC voltage commands
print('DC voltage commands')
slab.setVoltage(1,1.5)
slab.setVoltage(2,2.0)
v1=slab.readVoltage(1)
v2=slab.readVoltage(2)
v3=slab.readVoltage(3)
v4=slab.readVoltage(4)
if not( compare(v1,1.5) and compare(v2,2.0) and compare(v3,1.5) and compare(v4,1.5)):
    raise slab.SlabEx("setVoltage or readVoltage fail")  
print('  setVoltage and readVoltage pass')
slab.zero()
if not zeroCompare(slab.readVoltage(1),0.05):
    raise slab.SlabEx("zero command fails")
print('  zero pass')
print()

slab.setVoltage(1,1.0)
slab.setVoltage(2,1.0)
slab.dcPrint()
# Check dcPrint command if enabled
if check_dcPrint:
    slab.dcPrint()
    print('You should see volatages of all four ADCs')
    print('All should be about 1.0')
    slab.pause('(Press return)')   
    print()

#DC sweep command
#print('After measurement ends you shouls see four lines')
#print('ADCs 1,3,4 with equal X and Y values and ADC2 always 1.0')
#print('Close the window to continue')
#slab.dcSweepPlot(1,0.5,2.5,0.1)
print('DC Sweep test')
v=slab.dcSweep(1,0.5,2.5,0.1)
testPass = True
w=v[1]/v[0]
if not isVectorConstant(w,1.0):
    raise slab.SlabEx("dcSweep fails at DAC1 or ADC1")
w=v[3]/v[0]
if not isVectorConstant(w,1.0):
    raise slab.SlabEx("dcSweep fails at DAC1 or ADC3")
w=v[4]/v[0]
if not isVectorConstant(w,1.0):
    raise slab.SlabEx("dcSweep fails at DAC1 or ADC4")
if not isVectorConstant(v[2],1.0):
    raise slab.SlabEx("dcSweep fails at DAC2 or ADC2")
print('pass')    
print()

#Transient async test
print('Transient async check')
slab.setVoltage(1,1.0)
slab.setVoltage(2,2.0)
slab.setSampleTime(0.001)
slab.tranStore(100,4)
v=slab.transientAsync()
if not isVectorConstant(v[1],1.0):
    raise slab.SlabEx("transientAsync fails at ADC1")
if not isVectorConstant(v[2],2.0):
    raise slab.SlabEx("transientAsync fails at ADC2")
if not isVectorConstant(v[3],1.0):
    raise slab.SlabEx("transientAsync fails at ADC3")   
if not isVectorConstant(v[4],1.0):
    raise slab.SlabEx("transientAsync fails at ADC4")
print('  transientAsync pass')
print()

#Step response test
print('Step response check')
v=slab.stepResponse(1.0,2.0)
region1 = v[1][0:15]
region2 = v[1][25:100]
if not isVectorConstant(region1,1.0):
    raise slab.SlabEx("stepResponse fails") 
if not isVectorConstant(region2,2.0):
    raise slab.SlabEx("stepResponse fails")     
print('  stepResponse pass')
print()

# Single wave commands
print('Single wave test')
w1Values = slab.waveSine(1.0,2.0,100,returnList=True)
slab.setWaveFrequency(100)
slab.tranStore(100,1)
v = slab.waveResponse()
dif1 = v[1]-w1Values
if not isVectorZero(dif1,0.05):
    raise slab.SlabEx('waveResponse fails')
print('  waveResponse pass')
print()

# Dual wave commands
print('Dual wave test')
w2Values = slab.waveCosine(1.2,2.2,100,returnList=True,second=True)
slab.tranStore(100,2)
v = slab.waveResponse(dual=True)
dif1 = v[1]-w1Values
dif2 = v[2]-w2Values
if not isVectorZero(dif2,0.05):
    raise slab.SlabEx('dual waveResponse fails')
if not isVectorZero(dif1,0.05):
    raise slab.SlabEx('dual waveResponse fails')    
print('  dual waveResponse pass')    
print()

#DC Module test
print('DC Module test')
import slab_dc as dc
print('Close the window after drawing')
data=dc.curveVV(1.0,2.5,returnData=True)
if not isVectorConstant(data[0]/data[1],1.0):
    raise slab.SlabEx("curveVV fails") 
print('  curveVV pass')
print()

#AC Module test
print('AC Module test')
import slab_ac as ac
gain=ac.sineGain(1.0,2.0,100.0)
if not compare(gain,1.0):
    raise slab.SlabEx("sineGain fails")
print('  sineGain pass')
print()

# Meas module test
print('Meas module test')
import slab_meas as meas
slab.setWaveFrequency(100)
slab.tranStore(500,1)
v = slab.waveResponse()
p = meas.period(v[1],v[0])
if not compare(p,0.01):
    raise slab.SlabEx("period measurement fails")
print('  period measurement pass')    
    
# FFT module test
print('FFT module test')
import slab_fft as fft
slab.tranStore(5000,1)
v = slab.waveResponse()
g,f=fft.ftransform(v[1],v[0])
slab.plot11(f,ac.dB(np.absolute(g)),"Frequency plot for 100 Hz tone","Frequency (Hz)","dB")
    
print()
print('All tests passed')
print()




   







