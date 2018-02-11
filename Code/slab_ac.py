'''
AC submodule for the SLab project
It requires and imports slab.py

History:

Version 1.0 : First version (7/4/2017)

'''

import slab
import numpy as np                # Numpy for math calculations
import pylab as pl                # Pylab and Mathplotlib for plotting
import matplotlib.pyplot as plt
from scipy.optimize import leastsq

import math           # Math module
import numbers        # Numbers module

# Version information
version_major = 1
version_minor = 0
version_date  = "7/4/2017"

# Saturation limits
SAT_HIGH = 0.95
SAT_LOW  = 0.05


###################### INFO FOR THE HELP FILE ##########################

'''
@ac@
AC Submodule command topics: 
 
   f2w
   w2f
   dB
   magnitudePhase
   abs
   sineGain
   sineGainAll
   bodeResponse
   logRange
   plotFreq
   plotBode
   freqResponse
   freqResponseAll
'''


################ FREQUENCY RESPONSE COMMANDS ##################

'''
@f2w@
f2w(f)
Converts frequency from Hz to rad/s
Returns frequency in rad/s 
Included in slab_ac.py  
'''
def f2w(f):
    return f*2*math.pi
    
'''
@w2f@
w2f(w)
Converts frequency from rad/s to Hz
Returns frequency in Hz
Included in slab_ac.py  
'''    
def w2f(w):
    return w/(2*math.pi)
  
'''
@logRange@
logRange(start,end,ndec,ppd)
Generates a logarithmic spaced range of values

Parameters:
  start : start value
    end : end value
   ndec : number of decades
    ppd : points per decade  (defaults to 10)
    
Either the end or the ndec parameters must be supplied    
    
Returns a vector or values
Included in slab_ac.py    
    
Examples      
    >> f = logRange(fstart,fend)           # Range with default 10 ppd
    >> f = logRrange(fstary,fend,ppd=20)   # Range with 20 ppd
    >> f = logRrange(fstart,ndec=4)        # 4 decades with default 10 ppd
    >> f = logRange(fstrat,ndec=4,ppd=5)   # 4 decades with custom ppd
'''  
def logRange(start,end=0,ndec=0,ppd=10):   
    # Check if SciPy is loaded
    slab.checkSciPy() 
    
    stlog = np.log10(start)
    # We don't provide end 
    if end == 0:
        if ndec == 0:
            raise slab.SlabEx('Need to provide end or decades')  
        return 10**np.arange(stlog,stlog+ndec,1.0/ppd) 
    # We provide end
    endlog = np.log10(end)
    return 10**np.arange(stlog,endlog,1.0/ppd)

'''
@magPhase@
magPhase(value)
Computes magnitude and phase (deg) from complex value
Returns a tuple of magitude,phase
Included in slab_ac.py
''' 
def magPhase(value):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    ma = np.absolute(value)
    ph = np.angle(value,deg=True)
    return ma,ph    
  
'''
@mag@
mag(value)
Computes the absolute value (magnitude) from complex or real value
Returns a real magnitude value
Included in slab_ac.py
''' 
def mag(value):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    ma = np.absolute(value)
    return ma   

'''
@phase@
phase(value)
Computes the phase (deg) from complex value
Returns a real phase value
Included in slab_ac.py
''' 
def phase(value):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    ph = np.angle(value,deg=True)
    return ph      
  
'''
@dB@
dB(value)
Converts linear gain to dB
Returns dB value
Included in slab_ac.py
'''   
def dB(value):

    # Check if SciPy is loaded
    slab.checkSciPy() 
    
    return 20*np.log10(value)   
    
'''
@plotFreq@
plotFreq(f,v,labels)
Draws a frequency plot using a linear frequency axis

Required parameters
    f : Frequency vector or list of vectors (Hz)
    v : Complex vector or list of vectors
    
Optional parameters:
  labels : Labels for each curve
  
Returns nothing
Included in slab_ac.py  
    
If f and g are vectors only a curve is drawn
If f and g are lists of vectors, several curves will be drawn    
'''
def plotFreq(f,v,labels=[]):

    # Check if SciPy is loaded
    slab.checkSciPy()

    # Draw plot
    plt.figure(facecolor="white") # White border
    
    # Magnitude
    ax1 = pl.subplot(2,1,1)
    if isinstance(f[0],numbers.Number):
        pl.plot(f,np.absolute(v))
    else:    
        if labels == []:
            for fv,gv in zip(f,v):
                pl.plot(fv,np.absolute(gv))
        else:
            for fv,gv,lab in zip(f,g,labels):
                pl.plot(fv,np.absolute(gv),label=lab)
        
    pl.xlabel('Frequency (Hz)')   # Set X label
    pl.ylabel('Magnitude')        # Set Y label
    pl.title('Frequency plot')    # Set title
    
    if labels !=[]:
        pl.legend(loc='best') 
    pl.grid(True)
    
    # Phase
    ax2 = pl.subplot(2,1,2,sharex=ax1)
    if isinstance(f[0],numbers.Number):
        pl.plot(f, np.angle(v,deg=True))
    else:   
        if labels == []:    
            for fv,gv in zip(f,v):
                pl.plot(fv, np.angle(gv,deg=True))
        else:
            for fv,gv,lab in zip(f,v,labels):
                pl.plot(fv, np.angle(gv,deg=True), label=lab)

    pl.xlabel('Frequency (Hz)')   # Set X label
    pl.ylabel('Phase (deg)')      # Set Y label 
    if labels !=[]:
        pl.legend(loc='best')     
    pl.grid(True)    

    pl.show()   
    pl.close()        
    
'''
@plotBode@
plotBode(f,g,labels,linear)
Draws a bode plot
It uses a logarithmic frequency axe
By default it uses dB for the magnitude

Required parameters
    f : Frequency vector or list of vectors (Hz)
    g : Gain vector or list of vectors (Complex)
    
Optional parameters:
  labels : Labels for each curve
  linear : Use linear vertical axis instead of dB
  
Returns nothing
Included in slab_ac.py  
    
If f and g are vectors only a curve is drawn
If f and g are lists of vectors, several curves will be drawn    
'''
def plotBode(f,g,labels=[],linear=False):

    # Check if SciPy is loaded
    slab.checkSciPy()

    # Draw plot
    plt.figure(facecolor="white") # White border
    
    # Magnitude
    ax1 = pl.subplot(2,1,1)
    if isinstance(f[0],numbers.Number):
        if linear:
            pl.semilogx(f,np.absolute(g))
        else:
            pl.semilogx(f, dB(np.absolute(g))) 
    else:    
        if labels == []:
            for fv,gv in zip(f,g):
                if linear:
                    pl.semilogx(fv,np.absolute(gv))
                else:
                    pl.semilogx(fv,dB(np.absolute(gv)))
        else:
            for fv,gv,lab in zip(f,g,labels):
                if linear:
                    pl.semilogx(fv,np.absolute(gv),label=lab)
                else:
                    pl.semilogx(fv,dB(np.absolute(gv)),label=lab)
        
    pl.xlabel('Frequency (Hz)')   # Set X label
    if linear:
        pl.ylabel('Magnitude')        # Set Y label
        pl.title('Frequency plot')    # Set title
    else:
        pl.ylabel('Magnitude (dB)')   # Set Y label
        pl.title('Bode plot')         # Set title
    
    if labels !=[]:
        pl.legend(loc='best') 
    pl.grid(True)
    
    # Phase
    ax2 = pl.subplot(2,1,2,sharex=ax1)
    if isinstance(f[0],numbers.Number):
        pl.semilogx(f, np.angle(g,deg=True))
    else:   
        if labels == []:    
            for fv,gv in zip(f,g):
                pl.semilogx(fv, np.angle(gv,deg=True))
        else:
            for fv,gv,lab in zip(f,g,labels):
                pl.semilogx(fv, np.angle(gv,deg=True), label=lab)

    pl.xlabel('Frequency (Hz)')   # Set X label
    pl.ylabel('Phase (deg)')      # Set Y label 
    if labels !=[]:
        pl.legend(loc='best')     
    pl.grid(True)    

    pl.show()   
    pl.close()    
    
    
'''
@sineGain@
sineGain(v1,v2,freq,channel,npre,maxfs)
Calculates complex gain for a give frequency
Signal is generated at DAC1 and output is read at ADC1

Required parameters:
    v1 : min value of signal
    v2 : max value of signal
  freq : frequency (Hz)
  
Optional parameters:  
 channel : ADC channel to read (defaults to 1)
    npre : number of cycles before measurement (defaults to 5)
   maxfs : max sample frequency (at least 10*freq) 
           (Defaults to maximum reported by board)
        
Returns complex gain
Included in slab_ac.py        
'''
def sineGain(v1,v2,freq,channel=1,npre=5,maxfs=-1):
    #global adc_delay
    
    # Check if SciPy is loaded
    slab.checkSciPy()
    
    # No sat warning yet
    satWarn = False

    # Load defaults
    if maxfs == -1:
        maxfs = slab.maxSFfresponse
    # Checks
    if not slab.opened:
        raise slab.SlabEx("Not connected to board") 
    if v1 > v2:
        raise slab.SlabEx("Minimum value must be below maximum value")
    if maxfs > 1/slab.min_sample:
        raise SlabEx("Too high max sample frequency")
    if freq > maxfs/4.0:
        raise slab.SlabEx("Frequency too high")
        
    # This command is silent
    prev_verbose = slab.setVerbose(0)    
        
    # Create wave
    if maxfs > 200*freq:
        npoints = 200
        nsamples = 200
    else:
        npoints = int(maxfs/freq)
        nsamples = int(200/npoints) * npoints 
        npre = int(npre*npoints/nsamples)
        
    # Create test wave  
    amplitude = (v2 - v1) /2.0
    slab.waveSine(v1,v2,npoints)
    st = slab.setWaveFrequency(freq)
      
    # Perform measurement        
    slab.setTransientStorage(nsamples,1)
    time,out = slab.singleWaveResponse(channel,npre,tinit = 0.0)
    #time,out = waveResponse(npre,tinit = 0.0)
  
    # Check peak values
    vmax = slab.highPeak(out)
    vmin = slab.lowPeak(out)
    if (vmax/slab.vref) > SAT_HIGH or (vmin/slab.vref) < SAT_LOW:
        satWarn = True
  
    # Find best fit
    angles = np.array(range(0,nsamples))*2.0*np.pi/npoints
    # Initial guess
    mean0 = np.mean(out)
    amp0 = (vmax-vmin)/2.0
    phase0 = 0
    # Function to optimize
    optimize_func = lambda x: x[0]*np.sin(angles+x[1]) + x[2] - out
    # Perform optimization
    amp, phase, mean = leastsq(optimize_func, [amp0, phase0, mean0])[0]
    
    # Sync correction
    #factor = (st*np.pi*freq)/np.sin(st*np.pi*freq)
    #amp = amp*factor
    
    #print "Mean = " + str(mean)
    #print "Phase = " + str(phase)
    #print "Amplitude = " + str(amp)
    
    # Plot function
    #res = mean + amp*np.sin(angles+phase)
    #plot1n(angles,[out,res])

   
    # Restore verbose level
    slab.setVerbose(prev_verbose)
    
    # Warn if needed
    if satWarn:
        slab.warn("Saturated reading")
    
    return amp*np.cos(phase)/amplitude+1j*amp*np.sin(phase)/amplitude
  
      
'''
@sineGainAll@
sineGainAll(v1,v2,freq,npre,maxfs)
Calculates complex gain for a give frequency
Signal is generated at DAC1 and output is read at all ADCs

Required parameters:
    v1 : min value of signal
    v2 : max value of signal
  freq : frequency (Hz)
  
Optional parameters:  
    npre : number of cycles before measurement (defaults to 5)
   maxfs : max sample frequency (at least 10*freq) 
           (Defaults to maximum reported by board)
        
Returns list of complex gains (one for each ADC)
Included in slab_ac.py        
'''
def sineGainAll(v1,v2,freq,npre=5,maxfs=-1):
    #global adc_delay
    
    # Check if SciPy is loaded
    slab.checkSciPy()
    
    # No sat warning yet
    satWarn = False

    # Load defaults
    if maxfs == -1:
        maxfs = slab.maxSFfresponse
    # Checks
    if not slab.opened:
        raise slab.SlabEx("Not connected to board") 
    if v1 > v2:
        raise slab.SlabEx("Minimum value must be below maximum value")
    if maxfs > 1/slab.min_sample:
        raise slab.SlabEx("Too high max sample frequency")
    if freq > maxfs/4.0:
        raise slab.SlabEx("Frequency too high")
        
    # This command is silent
    prev_verbose = slab.setVerbose(0)    
        
    # Create wave
    if maxfs > 200*freq:
        npoints = 200
        nsamples = 200
    else:
        npoints = int(maxfs/freq)
        nsamples = int(200/npoints) * npoints 
        npre = int(npre*npoints/nsamples)
        
    # Create test wave  
    amplitude = (v2 - v1) /2.0
    slab.waveSine(v1,v2,npoints)
    st = slab.setWaveFrequency(freq)
      
    # Setup measurement        
    slab.setTransientStorage(nsamples,1)
    
    # Measure all channels
    list = []
    for channel in range(1,nadcs+1):
        time,out = slab.singleWaveResponse(channel,npre,tinit = 0.0)
  
        # Check peak values
        vmax = slab.highPeak(out)
        vmin = slab.lowPeak(out)
        if (vmax/slab.vref) > SAT_HIGH or (vmin/slab.vref) < SAT_LOW:
            satWarn = True
  
        # Find best fit
        angles = np.array(range(0,nsamples))*2.0*np.pi/npoints
        # Initial guess
        mean0 = np.mean(out)
        amp0 = (vmax-vmin)/2.0
        phase0 = 0
        # Function to optimize
        optimize_func = lambda x: x[0]*np.sin(angles+x[1]) + x[2] - out
        # Perform optimization
        amp, phase, mean = leastsq(optimize_func, [amp0, phase0, mean0])[0]
    
        # Warn if needed
        if satWarn:
            slab.warn("Saturated reading at ADC "+str(channel))
    
        # Gain to reported
        gain = amp*np.cos(phase)/amplitude+1j*amp*np.sin(phase)/amplitude
        
        # Add to list
        list.append(gain)
   
    # Restore verbose level
    slab.setVerbose(prev_verbose)
   
    # Return the list
    return list    
      
   
'''
@freqResponse@
freqResponse(v1,v2,fvector,channel,npre,maxfs):
Obtain the frequency response of a circuit
Signal is generated at DAC1 and output is read at ADC1

Required parameters:
       v1 : min value of signal
       v2 : max value of signal
  fvector : vector of frequencies to test
  
Optional parameters:  
 channel : Channel to measure (defaults to 1)
    npre : number of cycles before measurement (defaults to 5)
   maxfs : max sample frequency (at least 10*freq) 
          (Defaults to maximum reported by board)
    
Returns a vector of complex gains
Included in slab_ac.py    
'''    
def freqResponse(v1,v2,fvector,channel=1,npre=5,maxfs=-1):
    gvector = []
    for f in fvector:
        slab.message(1,"Measuring at " + str(f) + " Hz")
        gain = sineGain(v1,v2,f,channel,npre,maxfs)
        gvector.append(gain)
    if slab.scipy:
        return np.array(gvector)
    else:    
        return gvector    
        
'''
@freqResponseAll@
freqResponseAll(v1,v2,fvector,npre,maxfs):
Obtain the frequency response of a circuit for all channels
Signal is generated at DAC1 and output is read at all ADCs

Required parameters:
       v1 : min value of signal
       v2 : max value of signal
  fvector : vector of frequencies to test
  
Optional parameters:  
    npre : number of cycles before measurement (defaults to 5)
   maxfs : max sample frequency (at least 10*freq) 
          (Defaults to maximum reported by board)
    
Returns a vector of complex gains
Included in slab_ac.py   
'''    
def freqResponseAll(v1,v2,fvector,npre=5,maxfs=-1):
    glist = []
    for i in range(0,nadcs):
        glist.append([])
    for f in fvector:
        slab.message(1,"Measuring at " + str(f) + " Hz")
        gains = sineGainAll(v1,v2,f,npre,maxfs)
        for i in range(0,nadcs):
            glist[i].append(gains[i])

    if slab.scipy:
        rlist = []
        for g in glist:
            rlist.append(np.array(g))
        return rlist
    else:    
        return glist          
  
'''
Creates a bode plot excluding high frequency phase response
This functions shall be considered private and 
should not be called from outsise of this module
Parameters
    fvector : Frequency vector (Hz)
    gvector : Gain vector (Complex)
'''
def _plotBodeTrimmed(fvector,gvector):

    # Draw plot
    plt.figure(facecolor="white") # White border
    
    # Magnitude
    ax1 = pl.subplot(2,1,1)
    pl.semilogx(fvector, dB(np.absolute(gvector))) 
            
    pl.xlabel('Frequency (Hz)')   # Set X label
    pl.ylabel('Magnitude (dB)')   # Set Y label
    pl.title('Bode response plot')         # Set title
    pl.grid(True)
    
    # Remove high frequency phase
    hfreq = 1.0/(min_sample * 20.0)
    fv = []
    pv = []
    for f,g in zip(fvector,gvector):
        if f < hfreq:
            fv.append(f)
            pv.append(np.angle(g,deg=True))
    
    # Phase plot
    ax2 = pl.subplot(2,1,2,sharex=ax1)
    if fv != []:
        pl.semilogx(fv, pv)
        pl.xlabel('Frequency (Hz)')   # Set X label
        pl.ylabel('Phase (deg)')      # Set Y label 
        pl.grid(True)    

    pl.show()   
    pl.close()    
    
'''
@bodeResponse@
bodeResponse(v1,v2,fmin,fmax,ppd,channel,npre,maxfs,returnData)
Measures and draws a bode plot

Required parameters:
       v1 : min value of signal
       v2 : max value of signal
     fmin : minimum frequency
     fmax : maximum frequency
      
Optional parameters:  
     ppd : number of points per decade (defaults to 10)
 channel : ADC channel to use (defaults to 1)
    npre : number of cycles before measurement (defaults to 5)
   maxfs : max sample frequency (at least 10*freq) 
           (Defaults to maximum reported by board)
 returnData : Enable return of plot data (Defaults to False)           
 
Returns plot data if enabled (see also setPlotReturnData) 
    Tuple of two elements:
        Frequencies vector
        Complex gains vector

Included in slab_ac.py
'''    
def bodeResponse(v1,v2,fmin,fmax,ppd=10,channel=1,npre=5,maxfs=-1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy()

    fvector = logRange(fmin,fmax,ppd=ppd)
    gvector = freqResponse(v1,v2,fvector,channel,npre,maxfs)
    
    # Remove the trim of phase data
    #_plotBodeTrimmed(fvector,gvector)
    plotBode(fvector,gvector)
    if slab.plotReturnData or returnData:  
        return fvector,gvector    
 
################## CODE EXECUTED AT IMPORT #################### 
    
# Show version information upon load
slab.message(1,"SLab AC Submodule")
slab.message(1,"Version "+str(version_major)+"."+str(version_minor)+" ("+version_date+")")
slab.message(1,"")

     