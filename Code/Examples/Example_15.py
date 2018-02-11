'''
SLab Example
Example_15.py
Transient Async and Transient Triggered Examples
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

# Set storage
#   1000 points
#   3 ADCs (ADC1, ADC2, ADC3)
slab.setTransientStorage(1000,3)

# (A) Perform async transient read
slab.tranAsyncPlot()

# (B) Perform triggered read
slab.tranTriggeredPlot(1.6,slab.tmodeRise)

# Close serial communication
slab.disconnect()



    
