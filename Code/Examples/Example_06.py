'''
SLab Example
Example_06.py
Measure a voltage drop circuit

Connection diagram:

   <DAC1>----[A 1N4148 Diode K]----<ADC1>----<1k Resistor>----<GND>

'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab
import slab_dc as dc

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# Autodetects serial communication
slab.connect() 
        
# Draw Vo(Vi) plot using a default 0.1V step
dc.curveVV(0.0,3.0)

# Close serial communication
slab.disconnect()



    
