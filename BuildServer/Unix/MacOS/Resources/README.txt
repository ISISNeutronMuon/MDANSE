Installation instructions
=========================

MDANSE can be installed on Mac like any other software distributed via DMG file format:
 1) Double-click the DMG file to make its content available (the name will show up in the Finder sidebar),
    and a window generally opens also showing the content.
 2) Drag the application from the DMG window into the Applications directory to install (you may need an administrator password).
 3) Wait for the copy process to finish.
 4) Eject the DMG.
 5) Delete the DMG from the Downloads directory.

How to start MDANSE (the user interface)
========================================

MDANSE is currently not signed by an identified developer, so there are some extra steps you will
have to go through before you can use MDANSE like any other app. For more information, please see:
https://support.apple.com/en-gb/guide/mac-help/mh40616/mac
The gist of it is that the first time after installation, you will need to follow these steps:
 1) Right-click on MDANSE app and choose open
 2) Close the pop-up warning
 3) Again, right-click on MDANSE app and choose open
 4) Choose 'open anyway'

If this doesn't work, you might have to change some settings. This article might be of help:
https://www.macworld.co.uk/how-to/mac-app-unidentified-developer-3669596/

How to use the bundled python
=============================

TL;DR: always use /Applications/MDANSE.app/Contents/MacOS/python3

MDANSE comes with a bundled python that you can use to run scripts that use MDANSE. It has all the functionality
of a normal python installation, including several preinstalled libraries, most important of which are:
 - numpy
 - MMTK
 - Scientific
 - matplotlib
 - vtk

The python version is 2.7.18 and can be accessed through an executable script located at
/Applications/MDANSE.app/Contents/MacOS/python2 (/Applications is the installation directory)
There are two python files in the MacOS directory, but ONLY USE THE ONE CALLED python2!

The other python file, python, is the actual python executable, but it's missing some key
paths and so does not work as-is. The script you should use, python2, sets these automatically
and behaves almost exactly like a normal python executable. That said, if you have any issues
with the script, please let us know. In the meantime, you can use the following commands
in a bash (terminal) to use the bundled python:
 $ PARENT_DIR=/Applications/MDANSE.app/Contents
 $ export PYTHONHOME=$PARENT_DIR:$PARENT_DIR/Resources
 $ export PYTHONPATH=$PARENT_DIR/Resources/lib/python3.9:$PARENT_DIR/Resources:$PARENT_DIR/Resources/lib/python3.9/site-packages

Once these environment variables are set, you can use the proper python, though only in the
current bash session:
 $ /Applications/MDANSE.app/Contents/MacOS/python
