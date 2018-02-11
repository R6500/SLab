'''
SLab
Example_25.py
Analyze an astable
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab
import slab_meas as meas

import numpy as np

# Open serial communication
slab.connect() 
    
# Async Transient measurement
slab.setSampleTime(0.0001)
slab.setTransientStorage(1000,3)
slab.setPlotReturnData(True)
data = slab.tranAsyncPlot()

# Data analysis
meas.analyze(data)
      
# Close serial communication
slab.disconnect()

slab.pause()




    
