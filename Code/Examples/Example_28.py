'''
SLab
Example_28.py
Check a voltage divider
Uses the EZ module
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# Import and connect to the board
from slab_ez import *
     
# Get ADC 1 and ADC 2 data   
print "V1 " + str(readVoltage(1))
print "V2 " + str(readVoltage(2))
print "V1-2 " + str(readVoltage(1,2))











    
