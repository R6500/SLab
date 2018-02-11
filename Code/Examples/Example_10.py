'''
SLab Example
Example_10.py
BJT Transistor Ic(Ib)

Connection diagram:

   <DAC1>----<Ri 100k>---<ADC1>----<BASE>
   <Vdd>-----<Ro   1k>---<ADC2>----<COLLECTOR>
   <GND>-----<EMITTER>
   
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
        
slab.setDCreadings(50)        
        
# Transfer curve for low current
dc.transferCurveII(0.5,2.0,0.1,100.0)

# Transfer curve for high current
# Change Ri to 8k2 and Ro to 68
#slab.transferCurveII(1.0,3.0,0.1,8.2,0.068)

# Remove vbe
slab.zero()

# Close serial communication
slab.disconnect()



    
