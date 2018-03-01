'''
FFT curves submodule for the SLab project
It requires and imports slab.py

History:

Version 1.0 : First version (7/4/2017)
Version 1.1 : Compatibility with Python 3.x (1/3/2018)

'''

from __future__ import print_function

import slab
import slab_ac as ac

import numpy as np                # Numpy for math calculations
import pylab as pl                # Pylab and Mathplotlib for plotting
import matplotlib.pyplot as plt

import math           # Math module
import numbers        # Numbers module

# Version information
version_major = 1
version_minor = 0
version_date  = "7/4/2017"


###################### INFO FOR THE HELP FILE ##########################

'''
@fft@
FFT Submodule command topics:  

   ftransform
   distortion
'''

###################### FFT COMMANDS ##################   

'''
@ftransform@
ftransform(signal,time,ts)
Transforms from time to frequency domain
Uses the FFT of a signal but:
 1) Only positive frequencies are provided
 2) Factor 2/N applied except for DC that use 1/N

Parameters:
 signal : Signal to transform
   time : Time vector
     ts : Sample time
     
If neither time nor ts is provided, the command
will use the current sample time

Returns a tuple with:
   Complex amplitude vector
   Frequency vector
   
Included in slab_fft.py
'''
def ftransform(signal,time=[],ts=-1):
    if time != []:
        ts = time[1]-time[0]
    elif ts == -1:
        ts = sampleTime    

    data = np.fft.fft(signal)
    N = len(data)
    FI = 1/(ts*N)
    rv = []
    fv = []
    for i in range(0,N//2):
        if i == 0:
            rv.append(data[i]/N)
        else:
            rv.append(2*data[i]/N)
        fv.append(i*FI)
    return rv,fv        
   
'''
@distortion@
distortion(v1,v2,freq,show)
Generates sine wave at DAC1
Reads circuit output adt ADC1
Calculates four values related to distortion
Noise floor limits measurements

Required parameters:
    v1 : Minimum value of sine
    v2 : Maximum value of sine
  freq : Sine frequency
  
Optional parameters:
  show : Select if plots and text are shown
         (Defaults to True)
  
Returs a four element tuple:
   1) THD          (%)
   2) THD+ N       (%)   
   3) 2nd Harmonic (dBc)
   4) 3rd Harmonic (dBc)
   
Included in slab_fft.py
'''   
def distortion(v1,v2,freq,show=True):
    points = int(slab.maxSFfresponse/freq)
    if points > 100:
        points = 100
    if points < 50:
        raise slab.SlabEx("Frequency too high")
        
    cycles = 10    
    slab.waveCosine(v1,v2,points)
    slab.setWaveFrequency(freq)
    slab.tranStore(cycles*points)
    t,s = slab.singleWaveResponse()
    if show:
        slab.plot11(t,s,"Time plot","time(s)","ADC1(V)")
    c,f = ftransform(s,t) 
    if show:
        ac.plotFreq(f,c)
    
    # THD
    base = np.abs(c[cycles]) 
    tot = 0
    for i in range(2,7):
        tot = tot + np.abs(c[i*cycles])*np.abs(c[i*cycles]) 
    tot = np.sqrt(tot)
    print("tot: " +str(tot))
    thd = 100.0 * tot/base  
    
    # THD+N
    rms_total = std(s)
    rms_signal = base/np.sqrt(2.0)
    rms_no_signal = np.sqrt(rms_total*rms_total - rms_signal*rms_signal)
    thdn = 100.0 * rms_no_signal/rms_signal

    # Harmonic Distortion 2nd
    h2 = dB(np.abs(c[2*cycles])/base)
    
    # Harmonic Distortion 3rd
    h3 = dB(np.abs(c[3*cycles])/base)
    
    if show:
        print()
        print("THD   : " + str(thd) + " %")
        print("THD+N : " + str(thdn) + " %")
        print("Harmonic distortion 2nd : " + str(h2) + " dBc")
        print("Harmonic distortion 3rd : " + str(h3) + " dBc")
        print()
    
    return thd,thdn,h2,h3
    
################## CODE EXECUTED AT IMPORT ####################
  
# Show version information upon load
slab.message(1,"SLab FFT Submodule")
slab.message(1,"Version "+str(version_major)+"."+str(version_minor)+" ("+version_date+")")
slab.message(1,"")

    
    