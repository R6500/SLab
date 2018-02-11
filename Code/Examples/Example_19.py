'''
SLab Example
Example_19.py
Gain at a tone frequency
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

print "Response at 72Hz"
gain = ac.sineGain(1.0,2.0,72.0)
print "  Gain = " + str(gain)
m,p = ac.magnitudePhase(gain)
print "  Magnitude = " + str(m)
print "  Phase = " + str(p) + " deg"

slab.disconnect()

print
slab.pause("Hit RETURN to end the script")




    
