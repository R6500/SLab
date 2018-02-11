=====================
 SLab Example Folder
=====================

This folder contains examples for the SLab system with the same
numbering used in the PDF documentation

The "cmd spawn.bat" can be used in windows systems to open a command prompt
Once you have a prompt, you can use the "p.bat" file to call the Python interpreter 
and execute one of the examples, like:

  > p Example_01.py

As the SLab python files are not included on this directory some code is included inside
all examples to access the SLab files in the parent folder

   # Locate slab in the parent folder
   import sys
   sys.path.append('..')
   sys.path.append('.')

   # Set prefix to locate calibrations
   slab.setFilePrefix("../")

But you don't need to mess with that to just execute the examples


=======================
 List of SLab Examples
=======================

01 : Gets information about the connected board
02 : Prints all ADC voltages
03 : Measure of a forward diode curve
04 : Measure of a antiparallel diode curve
05 : Measure of a white LED in bridge mode
06 : Measure a voltage drop circuit
07 : Draws a Vo(Vi) plot with reference node
08 : Draws a Vo(Vi) hysteresis plot
09 : BJT Transistor Ic(Vbe)
10 : BJT Transistor Ic(Ib)
11 : Draws a NMOS set of curves
12 : Draws a NPN BJT set of curves
13 : Use of the generic plot commands
14 : Draws a NPN BJT Ib(Vbe) and Ic(Vbe)
15 : Transient Async and Transient Triggered Examples
16 : Step response of a RC low pass filter
17 : Plots the output of a filter at its corner frequency
18 : Plots the voltage and current of a capacitor
19 : Gain at a tone frequency
20 : Bode plot
21 : Draws bode plots
22 : Create several waveforms
23 : Comparison of real and ideal low pass filter
24 : Obtain differential voltages and currents
25 : Analyze an astable
26 : Diode Bridge measured with curveVVbridge
27 : Live change of a trimpot
28 : EZ Module : Check a voltage divider
29 : EZ Module : See how an LDR responds to light
30 : EZ Module : Check a voltage divider
31 : Generation of arbitrary waves
