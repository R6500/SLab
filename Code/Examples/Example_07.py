'''
SLab Example
Example_07.py
Draws a Vo(Vi) plot with reference node

Connection diagram:

   <DAC1>----<CUT Input>

   <CUT Output>----<ADC1>
   
   <Reference>-----<ADC2>
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab
import slab_dc  as dc

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# Autodetects serial communication
slab.connect() 
        
# Draw Vo(Vi) plot using a default 0.1V step
dc.curveVVref(0.0,3.0)

# Close serial communication
slab.disconnect()



    
