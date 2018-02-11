'''
SLab Calibration Stage 1
calibrate1.py

Obtain reference Vdd value
Performs a rough calibration on DAC 1
'''

import slab

slab.connect()

slab.manualCalibrateDAC1()

slab.disconnect()




    
