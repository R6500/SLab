'''
SLab Example
Example_24.py
Obtain differential voltages and currents

Setup

Vdd---<1k>---<ADC1>---<3k3>---<ADC2>---<1k>---<GND>
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab

# Set prefix to locate calibrations
slab.setFilePrefix("../")

slab.connect()

# (A) Calculate voltage on 3k3 resistor
vd = slab.readVoltage(1,2)
print "Voltage at 3k3 resistor is " + str(vd) + " V"

# (B) Calculate current on 3k3 resistor
i = slab.rCurrent(3.3,1,2)
print "Current at 3k3 resistor is " + str(i) + " mA"

i1 = slab.rCurrent(1.0,2,0)
print "Current at grounded 1k resistor is " + str(i) + " mA"

print
slab.disconnect()

slab.pause()



    
