'''
SLab Example
Example_21.py
Draws bode plots
'''

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab
import slab_ac as ac

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# (A) Response of a 100Hz lowpass
freq = ac.logRange(10.0,10000.0)
g1 = 1.0/(1.0+1j*freq/100.0)
ac.plotBode(freq,g1)

# (B) Response of a 100Hz lowpass and a 1kHz lowpass
g2 = 1.0/(1.0+1j*freq/1000.0)
ac.plotBode([freq,freq],[g1,g2],["100","1k"])




    
