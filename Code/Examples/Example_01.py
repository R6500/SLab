'''
SLab Example
Example_01.py
Gets information about the connected board
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# Autodetects serial communication
slab.connect() 
        
# Get board information
slab.printBoardInfo()

# Close serial communication
slab.disconnect()

# Pause the script to see the messages
slab.pause()

    
