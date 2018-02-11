'''
Analyze submodule for the SLab project
It requires and imports slab.py

History:

Version 1.0 : First version (7/4/2017)

'''

import slab
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
@meas@
Measure wave submodule command topics:

   analyze
   period
   tcross
'''   

################### PRIVATE HELPER FUNCTIONS ###########################
  
'''
Determine all times when a vector crosses value
Parameters:
  vector : Sequence of values
   value : Value to cross
    mode : Cross mode tmodeRise or tmodeFall 
Returns a list of indexes 
Included in slab_meas.py   
'''
def _xcross(vector,value,mode):
    if mode == slab.tmodeRise:
        pvalue = (value + slab.lowPeak(vector))/2.0
    else:
        pvalue = (value + slab.highPeak(vector))/2.0

    list = []
    
    preset = False
    for i in range(0,len(vector)):
        v = vector[i]
        if mode == slab.tmodeRise:
            if v < pvalue:
                preset = True
            if preset:
                if v > value:
                    list.append(i)
                    preset = False
        else:
            if v > pvalue:
                preset = True
            if preset:
                if v < value:
                    list.append(i)
                    preset = False
    return list  
   
   
################### ANALYSIS COMMANDS #############################
   
'''
@tcross@
tcross(vector,value,mode,time,ts)
Determine the times when a vector crosses a value

Required parameters:
  vector : Sequence of values
   value : Value to cross
   
Optional parameters:   
    mode : Cross mode tmodeRise (Default) or tmodeFall
    time : Optional time vector
      ts : Optional sample time  

Returns a vector of cross instants:
    Times if time vector is provided
    Time from Ts if provided
    Indexes if no time or Ts is provided 

Included in slab_meas.py    
'''
def tcross(vector,value,mode=slab.tmodeRise,time=[],ts=-1):
    listIn = _xcross(vector,value,mode)
    listOut = []
    if time != []:
        for element in listIn:
            listOut.append(time[element])
        return listOut
    if Ts != -1:
        for element in listIn:
            listOut.append(ts*element)
        return listOut
    return listIn  
    

'''
@period@
period(vector,time,ts,mode)
Compute the period of a signal

Period is computed from signal crossings at the halrange

Required parameters:
  vector : Sequence of values
   
Optional parameters:   
    time : Optional time vector
      ts : Optional sample time  
    mode : Cross mode tmodeRise (Default) or tmodeFall      

Returns a the mean period using:
    time vector if provided
    Ts if provided
    Samples indexes if no time or Ts is provided 

Included in slab_meas.py    
'''  
def period(vector,time=[],ts=-1,mode=slab.tmodeRise):
    m = slab.halfRange(vector)
    tlist = tcross(vector,m,mode,time,ts)
    n = len(tlist)
    if n < 2:
        raise slab.SlabEx("Not enough edges for period")
    sum = 0
    for i in range(0,n-1):
        sum = sum + tlist[i+1] - tlist[i]
    return sum/(n-1)   
    
'''
@analyze@
analyze(data)
Analize signal data and show results on screen

Optional parameters:
    data : data tuple to analyze
              Pos 0 : Time vector
              Pos 1 onward : Signal value vectors 
              
If data is not provided, a transientAsync command will be performed 

Returns nothing
Included in slab_meas.py         
'''    
def analyze(data=[]):
    # Perform measurement if no data is provided
    if len(data) == 0:
        data = slab.transientAsync()         
        vUnit = " V"
        tUnit = " s"
        fUnit = " Hz"
    else:
        vUnit = ""
        tUnit = ""
        fUnit = ""
        
    # Check if only one array/list is provided    
    if isinstance(data[0],numbers.Number):
        y = [data]
        x = range(0,len(data))  # Generate x vector
        tUnit = "samples"
    else:
        x = data[0]
        y = data[1:]
        print 
        print "Min time: " + str(x[0]) + tUnit
        print "Max time: " + str(x[-1]) + tUnit
        print "Total time: " + str(x[-1]-x[0]) +tUnit       
       
    print    
    for i in range(0,len(y)):
    
        print "Signal " + str(i+1)
        print "   Mean: " + str(slab.mean(y[i])) + vUnit
        print "   Std Dev: " + str(slab.std(y[i])) + vUnit
        print
        print "   High Peak: " + str(slab.highPeak(y[i])) + vUnit  
        print "   Low Peak: " + str(slab.lowPeak(y[i])) + vUnit 
        print "   Peak2peak: " + str(slab.peak2peak(y[i])) + vUnit
        print "   Half Range: " + str(slab.halfRange(y[i])) + vUnit
        print "   RMS: " + str(slab.rms(y[i])) + vUnit
        
        try:
            per = period(y[i],x)
        except:
            pass
        else:            
            print
            print "   Mean period: " + str(per) + tUnit
            print "   Mean frequency: " + str(1/per) + fUnit
            
        print
  
################## CODE EXECUTED AT IMPORT ####################
  
# Show version information upon load
slab.message(1,"SLab Analyze Submodule")
slab.message(1,"Version "+str(version_major)+"."+str(version_minor)+" ("+version_date+")")
slab.message(1,"")

 