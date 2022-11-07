
Using MDANSE Graphical User Interface
=====================================

Through the MDANSE graphical user interface (GUI), you will usually open
a trajectory, then specify the parameters for the analysis you wish to
perform and finally start the calculation itself. In this interface you
can also perform some other actions such as plotting the results of an
analysis, performing some file conversions, and view the geometrical
structure of your calculations. The GUI gives access to most of the
functionalities of MDANSE. Moreover, from the GUI it is possible to
create an input file for the command-line interface or an auto-start
analysis python script. Both kind of files provide a convenient starting
point to set up and run new analysis directly from the `command
line <#_Using_MDANSE_from>`__.

Opening MDANSE GUI
------------------

On all platforms, the GUI can be started either through an icon, or from
the command line. Below are outlined the subtleties connected to each
platform. In each case, it might take some time before the GUI opens, so
please be patient.

.. _windows-1:

Windows
~~~~~~~

If, during the installation, you selected to create a desktop shortcut,
you can use that to start MDANSE. Otherwise, you will have to open the
folder where you installed MDANSE (C:\\Program Files\\MDANSE by
default). Inside you can double click on the file called MDANSE with the
MDANSE icon:

.. image:: Pictures/picture6.png
   :width: 1.789cm
   :height: 1.727cm

.. image:: Pictures/picture7.png
   :width: 14.021cm
   :height: 0.467cm

Alternatively, you can double click the file called MDANSE_launcher.bat.
If you want to start MDANSE GUI from the command line, you just have to
type in the path to this batch file, not forgetting to use “ if there
are spaces in the path.

.. _macos-1:

MacOS
~~~~~

If you installed it normally, MDANSE icon should appear in Applications
like any other app. However, starting it the first time is a bit more
complicated since Apple implements stricter protections and we are not
registered as trusted developers. Therefore, you might have to change
some settings (see Ref [`4 <#SignetBibliographie_004>`__] for a guide).
Before you do that though, try simply opening MDANSE from the right
click menu (see Ref [`3 <#SignetBibliographie_003>`__] for a guide).

To start MDANSE GUI from terminal, you will have to run the following
command (change /Applications if you installed MDANSE elsewhere):

/Applications/MDANSE.app/Contents/MacOS/MDANSE

.. _linux-1:

Linux
~~~~~

If your distribution has an applications menu of some sort, like below,
you should be able to find an MDANSE icon in there that can be used to
start the GUI.

.. image:: Pictures/picture8.png
   :width: 12.314cm
   :height: 6.959cm

Otherwise, you will need to use the terminal. First, try running:

mdanse_gui

If that doesn’t work, you will need to know where MDANSE got installed.
By default, it should be in /usr/local, so try looking if the above
script is inside /usr/local/bin. If it isn’t there, the best bet is
searching for it with find / -name mdanse_gui. Once you know the path
(let’s call it mdanse_bin), run the following:

mdanse_bin/mdanse_gui
