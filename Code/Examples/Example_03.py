'''
SLab Example
Example_03.py
Measure of a forward diode curve

Circuit:

   <DAC 1>---<ADC 1>--<R 1k>---<ADC 2>---[A  1N4148 Diode K]-----<GND>

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
        
# Diode Curve
# We use the default 0.1V step and 1k resistor value
dc.curveVI(0.0,3.2)

# Close serial communication
slab.disconnect()



    
