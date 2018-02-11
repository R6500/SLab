'''
SLab Calibration Stage 3
calibrate3.py

Calibrates DACs using ADCs
ADCs must have been previously calibrated
'''

import slab

slab.connect()

slab.dacCalibrate()

slab.disconnect()




    
