'''
SLab Example
Example_14.py
Draws a NPN BJT Ib(Vbe) and Ic(Vbe)
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# Open serial communication
slab.connect() 

# Increase accuracy
slab.setDCreadings(50) 

# V Device curve
print "Performing measurements..."
#x,y1,y2,y3,y4 = slab.dcSweep(1,0.6,1.6,0.05)
x,y1,y2,y3,y4 = slab.dcSweep(1,1.0,3.0,0.1)

# Set DACs to zero
slab.zero()

# Post processing low current
#Ib = (x - y1)/100.0   # In mA
#Ic = (3.3 - y2)/1.0   # In mA
Ib = (x - y1)/6.8   # In mA
Ic = (3.3 - y2)/0.047   # In mA
beta = Ic/Ib

# Plot
print "Plotting"
slab.plot11(Ic,beta,"Beta vs Ic","Ic (mA)","Beta")

# Close serial communication
slab.disconnect()




    
