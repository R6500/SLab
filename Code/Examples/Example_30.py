'''
SLab
Example_30.py
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
     
# Live response 
sweepPlot()











    
