'''
SLab Example
Example_12.py
Draws a NPN BJT set of curves
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab
import slab_dc as dc

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# Open serial communication
slab.connect() 

#V Device curve
dc.iDeviceCurve(1.0,3.0,0.25,0.0,3.2,0.1,ri=330.0)

# Close serial communication
slab.disconnect()




    
