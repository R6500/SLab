'''
SLab Example
Example_13.py
Use of the generic plot commands
'''

import numpy as np

# Locate slab in the parent folder
import sys
sys.path.append('..')
sys.path.append('.')

import slab

# Set prefix to locate calibrations
slab.setFilePrefix("../")

# (A) Sin plot

x = np.arange(0,361,1)
y = np.sin(np.pi*x/180)

slab.plot11(x,y,"Sin plot","Angle (deg)","Sin(Angle)")

# (B) Sin,Cos plot

x = np.arange(0,361,1)
y1 = np.sin(np.pi*x/180)
y2 = np.cos(np.pi*x/180)

slab.plot1n(x,[y1,y2],"Sin and Cos plot","Angle (deg)","Sin,Cos(Angle)",["Sin","Cos"])

# (C) Sin,Cos plot
#     Different ranges and resolutions

x1 = np.arange(0,721,1)
y1 = np.sin(np.pi*x1/180)
x2 = np.arange(90,451,25)
y2 = np.cos(np.pi*x2/180)

slab.plotnn([x1,x2],[y1,y2],"Sin and Cos plot","Angle (deg)","Sin,Cos(Angle)",["Sin","Cos"])



    
