=======================================================
 SLab System v1.3 (1/3/2018)
=======================================================
 Code Folder Contents
=======================================================

readme.txt

  The file you are reading

license.txt

  SLab Python license information

SLab Python module ______________________________________

  The SLab Python modules are composed of several files:

         slab.py : Main SLab Python module (v1.1)
   SLab_Help.dat : Help file for the Python module
      slab_ac.py : Module for AC functions (v1.0)
      slab_dc.py : Module for DC functions (v1.0)
     slab_fft.py : Module for FFT related functions (v1.1)
    slab_meas.py : Module for no trivial measurements (v1.1)
      slab_ez.py : SLab easy module (v1.0)

Calibration files ______________________________________

  Those files perform the four stages of the hardware
  board calibration:

  Calibrate1.py : Stage 1 of board calibration
  Calibrate2.py : Stage 2 of board calibration
  Calibrate3.py : Stage 3 of board calibration
  Calibrate4.py : Stage 4 of board calibration

Batch files ____________________________________________

  Those files are provided for Windows users

  p.bat : Just calls the python interpreter
          If called from a command line, a Python file to
          execute can be included as the first argument like:
               > p calibrate1.py

  cmd spawn.bat : Creates a command line window on the 
                  current directory

  SLab_EZ.bat : Starts the SLab EZ module and connects to the board


Example folder _____________________________________________

  The example folder contains Python files associated to the
  examples shown on the SLab Python Reference document.
  See Examples.txt inside this folder


Misc Python files ___________________________________________

  Those files perform miscelaneous functions

    slabTest.py : Test suite for SLab (v1.0)
                  Checks basic SLab functionality 

        zero.py : Simple script that sets all DACs to zero

 board_check.py : Script to check the hardware board
                  Useful if you are not sure if your hardware
                  board is compliant with the SLab system

 generate_help.py : The SLab_Help.dat file is generated from the
                    contents of the slab.py file.
                    If you modify the slab.py file to add new functions
                    you will probably want to regenerate the help file
                    by calling this script.

