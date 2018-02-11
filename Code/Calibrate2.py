'''
SLab Calibration Stage 2
calibrate2.py

Calibrates ADCs using DAC 1
DAC 1 must have been previously calibrated
'''

import slab

slab.connect()

slab.adcCalibrate()

slab.disconnect()




    
