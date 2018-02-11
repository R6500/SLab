'''
SLab Example
Example_17.py
Plots the output of a filter at its corner frequency
R = 220nF
C = 10k
Tau = 2.2ms
wc = 454 rad/s
fc = 72 Hz
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# Open serial communication
slab.connect() 

# Set storage requirements
slab.setTransientStorage(100,2)

# Set wave
slab.waveSine(1.0,2.0,100)

# Set frequency
slab.setWaveFrequency(72.3)

# Measure
slab.wavePlot(10)

# Close serial communication
slab.disconnect()



    
