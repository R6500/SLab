'''
SLab Example
Example_20.py
Bode plot
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab
import slab_ac as ac

# Set prefix to locate calibrations
slab.setFilePrefix("../")

slab.connect()

# Bode response
ac.bodeResponse(0.5,2.5,10.0,8000.0,10,npre=5,maxfs=35000)

slab.disconnect()




    
