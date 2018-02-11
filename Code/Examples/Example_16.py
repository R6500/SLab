'''
SLab Example
Example_16.py
Step response of a RC low pass filter
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

# Set sample time to 50us
slab.setSampleTime(0.00005)

# Set storage requirements
slab.setTransientStorage(1000,2)

# Perform async transient read
result = slab.stepPlot(1.0,2.0)

# Close serial communication
slab.disconnect()



    
