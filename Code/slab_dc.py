'''
DC curves submodule for the SLab project
It requires and imports slab.py

History:

Version 1.0 : First version (7/4/2017)

'''

import slab
import numpy as np                # Numpy for math calculations
import pylab as pl                # Pylab and Mathplotlib for plotting
import matplotlib.pyplot as plt

import math           # Math module
import numbers        # Numbers module

# Version information
version_major = 1
version_minor = 0
version_date  = "7/4/2017"

###################### INFO FOR THE HELP FILE ##########################

'''
@dc@
DC Submodule command topics:

  curveVV
  curveVVref
  hystVVcurve
  curveVI
  curveVIref
  curveVIbridge
  transferCurveVI
  transferCurveII
  vDeviceCurve
  iDeviceCurve
  plotVI
'''

########################## COMMANDS #############################

'''
@plotVI@
plotVI(x,y,r,title,xl,yl)
Plots I(V) for a Device Under Test (DUT)

The following circuit shall be used

<X>----<R>----<Y>----<DUT>----GND

X is voltage in a series connection of resistor and DUT
Y is common node voltage between R and DUT

Required parameters:
   x : Vector with voltages
   y : Vector with voltage at common node
   r : Resistor value (in k Ohm)
   
Optional parameters:
    title : Plot title
       xt : Label for x axis
       yt : Label for y axis

Returns nothing  
Included in slab_dc.py      
'''
def plotVI(x,y,r,title="V-I Plot",xl="Voltage(V)",yl="Current (mA)"):
    curr = (x-y)/r
    
    # Check if SciPy is loaded
    slab.checkSciPy()  
    
    plt.figure(facecolor="white")   # White border
    pl.plot(y,curr)
    pl.xlabel(xl)
    pl.ylabel(yl)
    pl.title(title)
    pl.grid()
    pl.show()    
    pl.close()
    

'''
@curveVI@
curveVI(v1,v2,vi,r,wt,returnData)
Plots I(V) Device Curve

Perform a I(V) curve for a two terminal component
The following circuit shall be used

<DAC1>---ADC1---<R>---<ADC2>---<DUT>---GND

DAC1 forces a voltage in a series connection of resistor and DUT
ADC1 reads the voltage forced bu DAC1
ADC2 reads the voltage in the common node between R and DUT

Required parameters:
  v1 : Initial value of A2 (in Volt)
  v2 : End of range (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)
  r  : Resistor value in kohms (defaults to 1k)
  wt : Waiting time between steps (defaults to 0.1s)
  returnData : Enable return of plot data (Defaults to False)
  
Returns plot data if enabled (see also setPlotReturnData) 
Included in slab_dc.py 
''' 
def curveVI(v1,v2,vi=0.1,r=1.0,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    # Perform a DC sweep
    x,y1,y2,y3,y4 = slab.dcSweep(1,v1,v2,vi,wt)
    # Set DAC 1 to zero
    slab.writeChannel(1,0.0)
    # Plot result
    slab.message(1,"Drawing curve")
    vd = y2
    id = (y1 - y2) / r
    slab.plot11(vd,id,"V-I plot","Voltage (V)","Current (mA)")     
    
    if slab.plotReturnData or returnData:
        return vd,id
 
'''
@curveVIref@
curveVIref(v1,v2,vi,r,vr,wt,returnData)
Plots I(V) Device Curve with reference

Perform a I(V) curve for a two terminal component
The following circuit shall be used

<DAC1>---<ADC1>---<DUT>---ADC2--+--<R>-----<Vdd>
                                |
                                +--<R>-----<GND>          
                               
DAC1 forces a voltage on the positive terminal of the DUT
ADC1 reads the voltage forced by DAC1
ADC2 reads the voltage in negative terminal of the DUT
Device voltage Vd is calculated as Vadc1 - Vadc2
Device current Id is calculated as 2(Vdac2 - Vdd/2)/R

Required parameters:
  v1 : Initial value of DAC1 (in Volt)
  v2 : End of range (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)
  r  : Resistor value in kohms (defaults to 1k)
  vr : Reference voltage (defaults to Vdd/2)
  wt : Waiting time between steps (defaults to 0.1s)
  returnData : Enable return of plot data (Defaults to False)
  
Returns plot data if enabled (see also setPlotReturnData)
Included in slab_dc.py
''' 
def curveVIref(v1,v2,vi=0.1,r=1.0,vr=-1,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    # Perform a DC sweep
    x,y1,y2,y3,y4 = slab.dcSweep(1,v1,v2,vi,wt)
    # Set DAC 1 to Vdd/2
    slab.setVoltage(1,slab.vdd/2)
    # Plot result
    req =  r / 2
    if vr < 0:
        vr = slab.vdd / 2
    vd = y1 - y2
    id = (y2 - vr)/req
    slab.message(1,"Drawing curve")
    slab.plot11(vd,id,"V-I plot with reference","Voltage (V)","Current (mA)") 
    
    if slab.plotReturnData or returnData:
        return vd,id

 
'''
@curveVIbridgeOld@
curveVIbridge(v1max,v2max,vi=0.1,r=1.0,wt=0.1,returnData)
Plot I(V) Device Curve in bridge configuration

Perform a I(V) curve for a two terminal component
The following circuit shall be used

<DAC1>--<ADC1>---<R>---<ADC2>----<DUT>----<ADC3>----<DAC2>

Curve is measured in two sequences:

In the first sequence, DAC2 is set to zero
DAC1 forces a voltage in a series connection of resistor and DUT
ADC1 reads the voltage in the common node between R and DUT
Device voltage Vd is calculated as Vdac1 - Vr
Device current Id is calculated as (Vdac1 - Vadc1)/R
This first sequence is the same than in the curveVI command

In the second sequence, DAC1 is set to zero
DAC2 forces a voltage 
ADC1 reads the voltage in the common node between R and DUT

Required parameters:
  v1max : Max voltage at DAC 1 (in Volt)
  v2max : Max voltage at DAC 2 (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)
  r  : Resistor value in kohms (defaults to 1k)
  wt : Waiting time between steps (defaults to 0.1s)
  returnData : Enable return of plot data (Defaults to False)     
     
Returns plot data if enabled (see also setPlotReturnData)
Included in slab_dc.py
''' 
def curveVIbridgeOld(v1max,v2max,vi=0.1,r=1.0,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    # Perform first DC sweep
    slab.message(1,"Forward curve")
    slab.setVoltage(2,0.0)                            # Set DAC 2 to 0.0
    x,y1,y2,y3,y4 = slab.dcSweep(1,0.0,v1max,vi,wt)   # Sweep DAC 1

    # First plot
    vd = y2 - y3
    id = (y1 - y2)/r
    plt.figure(facecolor="white")   # White border
    pl.plot(vd,id)

    # Perform second DC sweep
    slab.message(1,"Backward curve")
    slab.setVoltage(1,0.0)                            # Set DAC 1 to 0.0
    x,y1,y2,y3,y4 = slab.dcSweep(2,0.0,v2max,vi,wt)   # Sweep DAC 2
    
    # Set DACs to zero
    slab.writeChannel(1,0.0)
    slab.writeChannel(2,0.0)
    
    # Second plot
    slab.message(1,"Drawing curve")
    vd = y2 - y3
    id = (y1 - y2)/r
    pl.plot(vd,id)
    
    pl.xlabel("Voltage (V)")
    pl.ylabel("Current (mA)")
    pl.title("V-I plot in bridge mode")
    pl.grid()
    pl.show() 
    pl.close()
    
    if slab.plotReturnData or returnData:
        return vd,id


'''
@curveVIbridge@
curveVIbridge(v1max,v2max,vi=0.1,vmin,r,wt,returnData)
Plot I(V) Device Curve in bridge configuration

Perform a I(V) curve for a two terminal component
The following circuit shall be used

<DAC1>--<ADC1>---<R>---<ADC2>----<+DUT->----<ADC3>----<DAC2>

Curve is measured in two sequences:

In the first sequence, DAC2 is set to vmin
DAC1 forces a voltage in a series connection of resistor and DUT
ADC1 reads the voltage in the common node between R and DUT
Device voltage Vd is calculated as Vadc2 - Vadc3
Device current Id is calculated as (Vadc1 - Vadc2)/R
This first sequence is the same than in the curveVI command

In the second sequence, DAC1 is set to vmin
DAC2 forces a voltage 
Measurements are the same

Required parameters:
  v1max : Max voltage at DAC 1 (in Volt)
  v2max : Max voltage at DAC 2 (in Volt)
  
Optional parameters:  
    vi : Step (defaults to 0.1V)
  vmin : Min DAC voltage (Defaults to 0 V)
    r  : Resistor value in kohms (defaults to 1k)
    wt : Waiting time between steps (defaults to 0.1s)
  returnData : Enable return of plot data (Defaults to False)     
     
Returns plot data if enabled (see also setPlotReturnData)
Included in slab_dc.py
''' 
def curveVIbridge(v1max,v2max,vi=0.1,vmin=0.0,r=1.0,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    # Perform first DC sweep
    slab.message(1,"Positive curve")
    slab.setVoltage(2,vmin)                                 # Set DAC 2 to vmin
    xf,y1f,y2f,y3f,y4f = slab.dcSweep(1,vmin,v1max,vi,wt)   # Sweep DAC 1

    # Perform second DC sweep
    slab.message(1,"Negative curve")
    slab.setVoltage(1,vmin)                                 # Set DAC 1 to vmin
    xr,y1r,y2r,y3r,y4r = slab.dcSweep(2,vmin,v2max,vi,wt)   # Sweep DAC 2
    
    # Set DACs to vmin
    slab.setVoltage(1,vmin)
    slab.setVoltage(2,vmin)
    
    # Join the curves
    vd=[]
    id=[]
    lenr=len(xr)
    for i in range(0,lenr):
        pos = lenr - i - 1
        vd.append(y2r[pos]-y3r[pos])
        id.append((y1r[pos]-y2r[pos])/r)
    for i in range(0,len(xf)):
        vd.append(y2f[i]-y3f[i])
        id.append((y1f[i]-y2f[i])/r)
    
    plt.figure(facecolor="white")   # White border
    pl.plot(vd,id)      
    pl.xlabel("Voltage (V)")
    pl.ylabel("Current (mA)")
    pl.title("V-I plot in bridge mode")
    pl.grid()
    pl.show() 
    pl.close()
    
    if slab.plotReturnData or returnData:
        return vd,id        
       
'''
@curveVV@
curveVV(v1,v2,vi,wt,adc2,returnData)
Plots a V(V) transfer curve

The following circuit shall be used

DAC1----<DUT In>  <DUT Out>-----ADC1

Vi is forced using the DAC1 
Vo is read at ADC1

Required parameters: 
  v1 : Initial value (in Volt)
  v2 : End of range (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)  
  wt : Waiting time between steps (defaults to 0.1s)
  adc2 : Use ADC2 to measure Vi (defaults to False)
  returnData : Enable return of plot data (Defaults to False)   
  
Returns plot data if enabled (see also setPlotReturnData)
Included in slab_dc.py
''' 
def curveVV(v1,v2,vi=0.1,wt=0.1,adc2=False,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    # Perform a DC sweep
    x,y1,y2,y3,y4 = slab.dcSweep(1,v1,v2,vi,wt)
    
    # Check ADC2 option
    if adc2:
        x = y2
    
    # Plot result
    slab.message(1,"Drawing curve")
    slab.plot11(x,y1,"V(V) Plot","Input (V)","Output(V)")
    
    if slab.plotReturnData or returnData:
        return x,y1
 
'''
@curveVVref@
curveVVref(v1,v2,vi,wt,adc3,returnData)
Plots a V(V) trasnfer curve with reference

Perform a Vo(Vi) curve using a ground reference
The following circuit shall be used

<DAC1>---<DUT In>  <DUT Out>---<ADC1>   <Ref>----<ADC2>

Vr is measured with ADC2
Vi is forced using the DAC1 and calculated as Vdac1 - Vref
Vo is read at ADC1 and calculated as Vadc2 - Vref

Required parameters: 
  v1 : Initial value (in Volt)
  v2 : End of range (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)  
  wt : Waiting time between steps (defaults to 0.1s)
  adc3 : Use ADC3 to sense Vi (Defaults to False)
  returnData : Enable return of plot data (Defaults to False)   
  
Returns plot data if enabled (see also setPlotReturnData)
Included in slab_dc.py
''' 
def curveVVref(v1,v2,vi=0.1,wt=0.1,adc3=False,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy()

    # Perform a DC sweep
    x,y1,y2,y3,y4 = slab.dcSweep(1,v1,v2,vi,wt)
    
    # Check ADC3 option
    if adc3:
        x = y3
    
    # Plot result
    slab.message(1,"Drawing curve")
    vi = x - y2
    vo = y1 - y2
    slab.plot11(vi,vo,"V(V) Plot with reference","Input (V)","Output(V)") 
    
    if slab.plotReturnData or returnData:
        return vi,vo
 

'''
@curveVVbridge@
curveVVbridge(vp,vn,vi,vmin,wt,returnData)
Plots a V(V) transfer curve in bridge configuration

The following circuit shall be used

DAC1---<ADC1>---<DUT In+>   <DUT Out>-----ADC3
DAC2---<ADC2>---<DUT In->   <DUT GND>-----ADC4

In+  is forced using DAC1 and read with ADC1 
In-  is forced using DAC2 and read with ADC2
Vo  is read at ADC3
GND is read at ADC4

Required parameters: 
  vp : Maximum positive voltage (in Volt)
  vn : Maximum negative voltage (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)  
  vmin : Minimum DAC voltage (Defaults to 0.0) 
  wt : Waiting time between steps (defaults to 0.1s)
  returnData : Enable return of plot data (Defaults to False)   
  
Returns plot data if enabled (see also setPlotReturnData)
Included in slab_dc.py
''' 
def curveVVbridge(vp,vn,vi=0.1,vmin=0.0,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy() 

    # Perform the positive DC sweep
    slab.message(1,"Positive curve")
    slab.setVoltage(2,vmin)
    xp,y1p,y2p,y3p,y4p = slab.dcSweep(1,vmin,vp,vi,wt)
    # Perform the negative DC sweep
    slab.message(1,"Negative curve")
    slab.setVoltage(1,vmin)
    xn,y1n,y2n,y3n,y4n = slab.dcSweep(2,vmin,vn,vi,wt)
    
    # Join all measurements
    x=[]
    y=[]
    
    ln = len(xn)
    for i in range(0,ln):
        pos = ln-i-1
        xvalue = y1n[pos]-y2n[pos]
        yvalue = y3n[pos]-y4n[pos]
        x.append(xvalue)
        y.append(yvalue)
        
    lp = len(xp)    
    for i in range(0,lp):
        xvalue = y1p[i]-y2p[i]
        yvalue = y3p[i]-y4p[i]
        x.append(xvalue)
        y.append(yvalue) 
        
    x = np.array(x)
    y = np.array(y)    
    
    # Plot result
    slab.message(1,"Drawing curve")
    slab.plot11(x,y,"V(V) Bridge Plot","Input (V)","Output (V)")
    
    if slab.plotReturnData or returnData:
        return x,y 
 
'''
@transferCurveVI@
transferCurveVI(v1,v2,vi,ro,wt,returnData)
Plots a I(V) Transfer Curve

The following circuit shall be used

<DAC1>---<Ri>---<ADC1>---<DUT In>

<Vdd>----<Ro>---<ADC2>---<DUT Out>

Ri is used to limit current and can be zero if needed. 
Show current entering DUT Out repect to ADC1 voltage

Required parameters:
  v1 : Initial value of DAC1 (in Volt)
  v2 : End of range (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)
  ro : Resistor Ro value in kohms (defaults to 1k)
  wt : Waiting time between steps (defaults to 0.1s)
  returnData : Enable return of plot data (Defaults to False)    
  
Returns plot data if enabled (see also setPlotReturnData)
Included in slab_dc.py
'''   
def transferCurveVI(v1,v2,vi=0.1,ro=1.0,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy()

    # Perform a DC Sweep
    x,y1,y2,y3,y4 = slab.dcSweep(1,v1,v2,vi,wt)
    # Set DAC to zero
    slab.writeChannel(1,0.0)
    # Calculate current
    curr = (slab.vdd - y2) / ro
    # Show curve
    slab.message(1,"Drawing curve")
    plt.figure(facecolor="white")   # White border
    pl.plot(y1,curr)
    pl.xlabel("Input (V)")
    pl.ylabel("Output(mA)")
    pl.title("DC I(V) Transfer Curve")
    pl.grid()
    pl.show()  
    pl.close()    
    
    if slab.plotReturnData or returnData:
        return y1,curr

'''
@transferCurveII@
transferCurveII(v1,v2,vi,r1,r2,wt,returnData)
Plots a I(I) transfer curve

The following circuit shall be used

<DAC1>---<R1>---<ADC1>---<DUT In>

<Vdd>----<R2>---<ADC2>---<DUT Out>

Show current entering DUT Out repect to current entering DUT In

Required parameters:
  v1 : Initial value of DAC1 (in Volt)
  v2 : End of range (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)
  wt : Waiting time between steps (defaults to 0.1s)
  r1 : Resistor R1 value in kohms (defaults to 1k)
  r2 : Resistor R2 value in kohms (defaults to 1k)
  returnData : Enable return of plot data (Defaults to False)    2
  
Returns plot data if enabled (see also setPlotReturnData)
Included in slab_dc.py
'''   
def transferCurveII(v1,v2,vi=0.1,r1=1.0,r2=1.0,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy()

    # Perform a DC Sweep
    x,y1,y2,y3,y4 = slab.dcSweep(1,v1,v2,vi,wt)
    # Set DAC to zero
    slab.writeChannel(1,0.0)  
    # Calculate current
    cin  = (x-y1) / r1
    cout = (slab.vdd - y2) / r2
    # Show curve
    slab.message(1,"Drawing curve")
    plt.figure(facecolor="white")   # White border
    pl.plot(cin,cout)
    pl.xlabel("Input (mA)")
    pl.ylabel("Output (mA)")
    pl.title("DC I(I) Transfer Curve")
    pl.grid()
    pl.show()   
    pl.close()
    
    if slab.plotReturnData or returnData:
        return cin,cout 
 
 
'''
@vDeviceCurve@
vDeviceCurve(vi1,vi2,vii,vo1,vo2,voi,ro,wt)
Measures and plots V Device Output Curves

Draws curves for a device with voltage input
The following circuit shall be used:

<DAC2>---<Ri>---<ADC1>----<DUT1>

<DAC1>---<Ro>---<ADC2>----<DUT2>

R1 is used to limit current but it can be ommited

Required parameters:
  vi1 : Initial voltage for input (DAC2)
  vi2 : End of range for input
  vii : Step for input
  vo1 : Initial voltage for output (DAC1)
  vo2 : End of range for output
  
Optional parameters:  
  voi : Step for output (Defaults to 0.1V)
   ro : Output resistance in kohms (Defaults to 1k)
   wt : Wait time between measurements (Defaults to 0.1s)
 
Returns nothing
Included in slab_dc.py
'''    
def vDeviceCurve(vi1,vi2,vii,vo1,vo2,voi=0.1,ro=1.0,wt=0.1):

    # Check if SciPy is loaded
    slab.checkSciPy()

    i_range=np.arange(vi1,vi2,vii)
    o_range=np.arange(vo1,vo2,voi)
    plt.figure(facecolor="white")   # White border
    for vi in i_range:
        avo = []
        aio = []
        slab.setVoltage(2,vi)
        slab.wait(wt)
        a0 = slab.readVoltage(1)
        for vs in o_range:
            slab.setVoltage(1,vs)
            slab.wait(wt)
            a1 = slab.readVoltage(2)
            a2 = slab.readVoltage(3)
            curr = (a1 - a2) / ro
            avo.append(a2)
            aio.append(curr)
        lbl = "{:.3f}".format(a0) + ' V'    
        pl.plot(avo,aio,label=lbl)
    slab.message(1,"Drawing curves"    )
    pl.legend(loc='upper right')    
    pl.title("Io(Vo) Device Curves as function of Vi")
    pl.xlabel("Output Voltage(V)")
    pl.ylabel("Output Current(mA)")  
    pl.grid()    
    pl.show()    
    pl.close()
   
'''
@iDeviceCurve@
iDeviceCurve(vi1,vi2,vii,vo1,vo2,voi,ri,ro,wt)
Measures and plots I Device Output Curves

Draws curve for a device with current input
The following circuit shall be used:

<DAC2>----<Ri>---<ADC1>---<DUT1>

<DAC1>---<ADC2>---<Ro>---<ADC3>---<DUT2>

Required parameters:
  vi1 : Initial voltage for input 
  vi2 : End of range for input
  vii : Step for input
  v01 : Initial voltage for output 
  v02 : End of range for output
  
Optional parameters:  
  voi : Step for output
   ri : Input resistance
   ro : Output resistance
   wt : Wait time between measurements (default to 0.1s)
   
Returns nothing
Included in slab_dc.py  
'''    
def iDeviceCurve(vi1,vi2,vii,vo1,vo2,voi=0.1,ri=1.0,ro=1.0,wt=0.1):

    # Check if SciPy is loaded
    slab.checkSciPy()

    i_range=np.arange(vi1,vi2,vii)
    o_range=np.arange(vo1,vo2,voi)
    plt.figure(facecolor="white")   # White border
    for vi in i_range:
        avo = []
        aio = []
        slab.setVoltage(2,vi)
        slab.wait(wt)
        a0 = slab.readVoltage(1)
        i_in = (vi - a0) / ri
        for vs in o_range:
            slab.setVoltage(1,vs)
            slab.wait(wt)
            a1 = slab.readVoltage(2)
            a2 = slab.readVoltage(3)
            curr = (a1 - a2) / ro
            avo.append(a2)
            aio.append(curr)
        lbl = "{:.6f}".format(i_in) + ' mA'    
        pl.plot(avo,aio,label=lbl)   
    slab.message(1,"Drawing curves")
    pl.legend(loc='upper right')         
    pl.title("Io(Vo) Device Curves as function of Ii")
    pl.xlabel("Output Voltage(V)")
    pl.ylabel("Output Current(mA)")   
    pl.grid()    
    pl.show()   
    pl.close()    
 
 
'''
@hystVVcurve@
hystVVcurve(v1,v2,vi,wt,returnData)
V(V) Transfer Hysteresis Curve

The following circuit shall be used

<DAC1>----<DUT In>  <DUT Out>-----<ADC1>

Vi is forced using the DAC1 
Vo is read at ADC1

Required parameters: 
  v1 : Initial value (in Volt)
  v2 : End of range (in Volt)
  
Optional parameters:  
  vi : Step (defaults to 0.1V)  
  wt : Waiting time between steps (defaults to 0.1s)
  returnData : Enable return of plot data (Defaults to False)    
  
Returns plot data if enabled (see setPlotReturnData)
Included in slab_dc.py    
''' 
def hystVVcurve(v1,v2,vi=0.1,wt=0.1,returnData=False):

    # Check if SciPy is loaded
    slab.checkSciPy()

    # Perform DC sweeps
    xf,y1f,y2f,y3f,y4f = slab.dcSweep(1,v1,v2,vi,wt)
    xr,y1r,y2r,y3r,y4r = slab.dcSweep(1,v2,v1,-vi,wt)
    # Plot result
    slab.message(1,"Drawing curves")
    plt.figure(facecolor="white")     # White border
    pl.plot(xf,y1f,label="Forward");
    pl.plot(xr,y1r,label="Back");
    pl.legend(loc='lower right')         
    pl.title("V(V) Hysteresis Curve")
    pl.xlabel("Input Voltage(V)")
    pl.ylabel("Output Voltage(V)")   
    pl.grid()    
    pl.show()   
    pl.close()

    if slab.plotReturnData or returnData:
        return xf,y1f,xr,y1r   

        
################## CODE EXECUTED AT IMPORT ####################
 
# Show version information upon load
slab.message(1,"SLab DC Submodule")
slab.message(1,"Version "+str(version_major)+"."+str(version_minor)+" ("+version_date+")")
slab.message(1,"")

 