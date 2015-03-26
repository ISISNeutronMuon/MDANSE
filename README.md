MDANSE (Molecular Dynamics Analysis for Neutron Scattering Experiments) is a python library/application for analysis molecular dynamics simulation data

This is nMoldyn-3.0.12, an interactive program for the
analysis of Molecular Dynamics trajectories. This program is
copyrighted but free to use for anyone under the CeCILL license,
see the file LICENSE for details.

nMoldyn should work with all major variants of Unix, including Linux
and MacOSX and Windows. There is little system-specific code in nMoldyn 
itself, so porting nMoldyn to other systems should be straightforward.
However, we cannot provide any support for this.

If you have any questions about nMoldyn that are not answered on the
Web page mentioned above, please contact the authors.


Eric Pellegrini
Calcul Scientific
Institut Laue Langevin
6 Rue Jules Horowitz
38042 Grenoble
France
E-Mail: pellegrini@ill.fr

Konrad Hinsen
Centre de Biophysique Moleculaire (CNRS)
Rue Charles Sadron
45071 Orleans Cedex 2
France
E-Mail: hinsen@cnrs-orleans.fr

Gerald Kneller
Centre de Biophysique Moleculaire (CNRS)
Rue Charles Sadron
45071 Orleans Cedex 2
France
E-Mail: kneller@cnrs-orleans.fr

Step 1: Prerequesites
=====================

Before installing nMOLDYN make sure that the following components are installed
and configured properly:

	-Tcl and Tk libraries version >= 8.4

	-Python 2.4 or higher
	-numpy version >= 1.2
	-matplotlib version >= 0.98
	-pyro version >= 3.9
	-Scientific version >= 2.8
	-MMTK version >= 2.6.1

    -NetCDF library version >= 3.6.1
     To check for that, in a terminal, type

         python -c 'import Scientific.IO.NetCDF'

     If you get no error message NetCDF is likely to be properly installed and 
     configured on your system.


Step 2: installation
====================

In a terminal, type the following instructions in the directory where you untared
the nMOLDYN archive:

    cd nMOLDYN-3.X.Y
    python setup.py build
    python setup.py install

The last command may require administrator privileges.


Step 3: running nMOLDYN
=======================

Once the installation is completed run nMOLDYN by typing

	./nMOLDYNStart.py
	
in your Python binaries directory.

In the future, you should create an alias/shortcut for that script in order to not 
disrupt any component of that sensitive directory.

WARNING:
========

If the version of Scientific used to run nMOLDYN is the 2.9.0, small changes has 
to be performed in order to use nMOLDYN in parallel mode via a Pyro server.

The changes are the following:

FILE    : MasterSlave.py
LOCATION: Scientific installation directory

REPLACE

def getMachineInfo():
    import os
    sysname, nodename, release, version, machine = os.uname()
    pid = os.getpid()
    return "PID %d on %s (%s)" % (pid, nodename, machine)

BY

def getMachineInfo():
    import os
    import platform
    sysname, nodename, release, version, machine, processor = platform.uname()
    pid = os.getpid() 
    return "PID %d on %s (%s)" % (pid, nodename, machine)

If you are not familiar with the Python installed modules file structure, you
can find the path for Scientific directory by running the following command 
within the Python interpreter:

import Scientific
print Scientific.__path__[0]

KNOWN BUGS:
===========

    - Bug with tk >= 8.5 on Linux (Fedora, Suse, Ubuntu): when using a tkMessageBox, if you click 'Yes' 
    the answer will be the same as 'No'! In nMOLDYN, you will experience this bug at the end of an 
    analysis when you can decide to plot the results just after the analysis. Whatever is your decision 
    ('Yes' or 'No'), no plot will be displayed.
    
    Here is the proposed patch (http://bugs.python.org/issue4961):
    
    Index: Lib/lib-tk/tkMessageBox.py
    ===================================================================
    --- Lib/lib-tk/tkMessageBox.py	(revision 73494)
    +++ Lib/lib-tk/tkMessageBox.py	(working copy)
    @@ -70,11 +70,13 @@
         if title:   options["title"] = title
         if message: options["message"] = message
         res = Message(**options).show()
    -    # In some Tcl installations, Tcl converts yes/no into a boolean
    +    # In some Tcl installations, yes/no is converted into a boolean.
         if isinstance(res, bool):
    -        if res: return YES
    +        if res:
    +            return YES
             return NO
    -    return res
    +    # In others we get a Tcl_Obj.
    +    return str(res)
 
     def showinfo(title=None, message=None, **options):
         "Show an info message"
    

