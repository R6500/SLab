'''
SLab Example
Example_08.py
Draws a Vo(Vi) hysteresis plot 

Connection diagram:

   <DAC1>----<CUT Input>

   <CUT Output>----<ADC1>
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
dc.hystVVcurve(0.0,3.2)

# Draw Vo(Vi) plot using a fine step in a reduced range
dc.hystVVcurve(1.2,2.0,0.01)

# Close serial communication
slab.disconnect()



    
