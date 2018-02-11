'''
Generates the help file from the source code
'''

HELP_FILE = "SLab_Help.dat"
COMMAND_LIST = "SLab_Commands.txt"

def processFile(filename,hfile,cfile):
    print "Processing " + filename
    cfile.write("FILE: "+filename+"\n")
    with open(filename, 'r') as sfile:
        copy = False
        for line in sfile:
            if line.startswith("@"):
                hfile.write(line)
                cfile.write("  "+line)
                copy = True
            elif line.startswith("'''"):
                copy = False
            elif copy:
                hfile.write(line)   

print
print "Working on " + HELP_FILE + " ..."

with open(HELP_FILE, 'w') as hfile:
    with open(COMMAND_LIST, 'w') as cfile:

        processFile("slab.py",hfile,cfile)
        processFile("slab_dc.py",hfile,cfile)
        processFile("slab_ac.py",hfile,cfile)
        processFile("slab_meas.py",hfile,cfile)
        processFile("slab_fft.py",hfile,cfile)
        processFile("slab_ez.py",hfile,cfile)
    
        hfile.write("@# EOF\n") 
    
print "Done"
print
                