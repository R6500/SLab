'''
SLab
Example_31.py
Generation of arbitrary waves
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab
import numpy as np

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# Connect to board
#slab.connect()

# Creates a new constant wave
def arbNew(np,value=0):
    listx = []
    listy = []
    for point in range(0,np):
        listx.append(point)
        listy.append(value)
    return listx,listy

# Set a constant region in a wave
def arbConst(list,start,stop,value):
    for point in range(start,stop+1):
        list[point]=value
   
# Set a linear region in a wave
def arbLinear(list,start,stop,v1,v2):
    for point in range(start,stop+1):
        list[point]=v1+(v2-v1)*(point-start)/(stop-start)
   
# Set a triangle region in a wave
def arbTriangle(list,start,stop,v1,v2):
    half = start + (stop-start)/2
    for point in range(start,stop+1):
        if point < half:
            list[point]=v1+(v2-v1)*(point-start)/(half-start) 
        else:
            list[point]=v2+(v1-v2)*(point-half)/(stop-half) 
   
# Set an elyptical region in a wave
def arbEllipse(list,start,stop,v1,v2):
    radius = (stop - start)/2
    center = (start+stop)/2
    mult = (v2-v1)/radius
    for point in range(start,stop+1):
        distance = point-center
        list[point]=v1+mult*np.sqrt(radius*radius-distance*distance)
        
# Set an elyptical sector in a wave
def arbSectA(list,start,stop,v1,v2):
    radius = (stop - start)
    center = stop
    mult = (v2-v1)/radius
    for point in range(start,stop+1):
        distance = point-center
        list[point]=v1+mult*np.sqrt(radius*radius-distance*distance)    

# Set an elyptical sector in a wave
def arbSectB(list,start,stop,v1,v2):
    radius = (stop - start)
    center = start
    mult = (v2-v1)/radius
    for point in range(start,stop+1):
        distance = point-center
        list[point]=v1+mult*np.sqrt(radius*radius-distance*distance)        
   
# MAIN CODE ############################################################
       
# Create wave
wavex,wavey = arbNew(10000,1)

#arbConst(wavey,200,600,2)
#arbLinear(wavey,800,1200,1.5,2.5)
#arbTriangle(wavey,1400,1800,1.5,2.5)
#arbEllipse(wavey,2000,2400,1.5,2.5)
#arbEllipse(wavey,2500,3000,2.5,1.5)

wavex1,wavey1=arbNew(10000,1)
#House
arbTriangle(wavey1,1000,5000,2.0,3.0)
arbConst(wavey1,1300,2000,2.7)
#Car
arbSectA(wavey1,6000,7000,1.0,1.2)
arbSectB(wavey1,8500,9000,1.0,1.2)
arbConst(wavey1,7000,8500,1.4)

wavex2,wavey2=arbNew(10000,1)
arbConst(wavey2,2000,4000,1.5)
#Car
arbEllipse(wavey2,6500,7000,1.0,0.9)
arbEllipse(wavey2,8000,8500,1.0,0.9)

# Show wave   
slab.plot1n(wavex1,[wavey1,wavey2])     
    
# Connect to board
slab.connect()  

# Upload wave
slab.loadWavetable(wavey1)
slab.loadWavetable(wavey2,second=True)
slab.setWaveFrequency(2.0)

# Show wave
slab.wavePlay(40,dual=True)
    
# Disconnect
slab.disconnect()
