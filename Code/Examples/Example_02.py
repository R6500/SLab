'''
SLab Example
Example_02.py
Prints all ADC voltages
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
        
# Print ADC voltages
slab.dcPrint()

# Close serial communication
slab.disconnect()

slab.pause()



    
