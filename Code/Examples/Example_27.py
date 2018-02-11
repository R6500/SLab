'''
SLab
Example_27.py
Live change of a trimpot

We will use a 10k trimpot
Connect the resistor ends to Vdd and GND
Connect the cursor to ADC 1
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

print 
print "Use CTRL+C to end"
print    
    
# Live information of ADC 1 readings    
slab.dcLive(1)   

# Disconnect from the board
slab.disconnect()







    
