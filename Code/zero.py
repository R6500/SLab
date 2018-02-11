'''
SLab
zero.py
Executes the zero command so that all DACs are set to minimum voltage
'''

import slab

# Autodetects serial communication
slab.connect() 
        
# Issue the zero command
slab.zero()

print "Zero command issued"
print "You can now disconnect the supply"
print

# Close serial communication
slab.disconnect()



    
