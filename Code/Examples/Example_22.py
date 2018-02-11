'''
SLab Example
Example_22.py
Create several waveforms

Connect DAC 1 to ADC 1
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

# Set sample time to 100us
slab.setSampleTime(0.0001)

# Set storage requirements
slab.setTransientStorage(200,1)

# (A) Creates and measures a square wave
slab.waveSquare(1.0,2.0,100)
slab.wavePlot()

# (B) Creates and measures a triangle wave
slab.waveTriangle(1.0,2.0,100)
slab.wavePlot()

# (C) Creates and measures a sawtooth wave
slab.waveSawtooth(1.0,2.0,100)
slab.wavePlot()

# (D) Creates and measures a sine wave
slab.waveSine(1.0,2.0,100)
slab.wavePlot()

# (E) Creates and measures a 10% duty pulse wave
slab.wavePulse(1.0,2.0,100,90)
slab.wavePlot()

# (F) Creates and measures a staircase waveform
list = []
for i in range(0,10):
    for j in range(0,10):
        list.append(1.0+0.1*i)
slab.loadWavetable(list)

slab.wavePlot()

# (G) Creates and measures a cosine wave
slab.waveCosine(1.0,2.0,100)
slab.wavePlot()

# (H) Creates and measures a noise wave
slab.waveNoise(1.5,0.1,100)
t,a1 = slab.wavePlot(1,returnData=True)
print "Std Dev is " + str(slab.std(a1)) + " V"

# (I) Creates and measures a random wave between 1V and 2V
slab.waveRandom(1,2,100)
slab.wavePlot()

# Close serial communication
slab.disconnect()




    
