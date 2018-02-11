'''
SLab Example
Example_18.py
Plots the voltage and current of a capacitor
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
time,v1,v2 = slab.waveResponse(10)

# Compute current
ic = v1-v2   # In mA * 10

# Show plot
slab.plot1n(time,[v2,ic],"Capacitor","time (s)","Vc (V) & Ic (mA)",["Vc","Ic x 10"])

# Close serial communication
slab.disconnect()



    
