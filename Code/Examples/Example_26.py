'''
SLab
Example_26.py
Diode Bridge measured with curveVVbridge
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
    
# Reduce measurement noise by averaging    
slab.setDCreadings(10)    

# Curve with vmin = 0    
dc.curveVVbridge(3.2,3.2,wt=0.3,vmin=0.2)






    
