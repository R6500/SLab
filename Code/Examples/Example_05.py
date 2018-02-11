'''
SLab Example
Example_05.py
Measure of a white LED in bridge mode

Circuit:

   <DAC 1>---<ADC 1>---<R 1k>---<ADC 2>---[A  White LED K]---<ADC 3>---<DAC 2>

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
        
# Increase number of measurements
slab.setDCreadings(400)        

# Diode Curve
# We use the default 0.1V step and 1k resistor value
# We also set the minimum voltage to 0.2V
dc.curveVIbridge(3.2,3.2,vmin=0.2)

# Close serial communication
slab.disconnect()



    
