'''
SLab Example
Example_11.py
Draws a NMOS set of curves
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

#Roundings
slab.setDCreadings(10)

#V Device curve
dc.vDeviceCurve(2.2,3.2,0.2,0.0,3.2,0.1)

# Close serial communication
slab.disconnect()




    
