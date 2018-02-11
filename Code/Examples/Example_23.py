'''
SLab Example
Example_23.py
Comparison of real and ideal low pass filter
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab
import slab_ac as ac

# Set prefix to locate calibrations
slab.setFilePrefix("../")

slab.connect()

# Frequencies to test
fv = ac.logRange(10.0,8000.0,10.0) 

# Ideal response
R = 10000.0
C = 220.0e-9
#C = 100.0e-9
#C = 10.0e-6

fc = ac.w2f(1/(R*C)) 
g0 = 1.0/(1.0+1j*fv/fc)

# Real response
g = ac.freqResponse(0.5,2.5,fv,npre=5,maxfs=35000)

# Plot of both curves
ac.plotBode([fv,fv],[g0,g],["Ideal","Real"])

slab.disconnect()




    
