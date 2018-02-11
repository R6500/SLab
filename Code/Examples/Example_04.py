'''
SLab Example
Example_04.py
Measure of a antiparallel diode curve

Circuit:

   <DAC 1>---<ADC 1>--+--[A  1N4148 Diode K]----+--<ADC 2>--+--<R 1k>---<Vdd>
                      |                         |           |
                      +--[K  1N4148 Diode A]----+           +--<R 1k>---<GND>

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
        
# Increase precission
slab.setDCreadings(400)        
        
# Diode Curve
# We use the default 0.1V step and 1k resistor value
dc.curveVIref(0.0,3.2)

# Obtain reference voltage
print
print "Disconnect the DAC1 line"
slab.pause()
print

# Get reference voltage
vrf = slab.readVoltage(2)
print "Reference voltage is "+str(vrf)+" Volt"

print
print "Reconnect the DAC1 line"
slab.pause()
print

# More precise curve
dc.curveVIref(0.0,3.2,vr=vrf)

# Close serial communication
slab.disconnect()



    
