'''
SLab Example
Example_09.py
BJT Transistor Ic(Vbe)

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
        
# Transfer curve
#slab.TransferCurveVI(0.5,3.0,0.02)
dc.transferCurveVI(1.0,3.0,vi=0.1,wt=0.1,ro=0.068)

# Remove vbe
slab.zero()

# Close serial communication
slab.disconnect()



    
