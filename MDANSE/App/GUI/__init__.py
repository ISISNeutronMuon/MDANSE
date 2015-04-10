import os
import platform

# Hack for the (in)famous "(python:865): LIBDBUSMENU-GLIB-WARNING **: Trying to remove a child that doesn't believe we're it's parent."
if platform.dist()[0].lower() == "ubuntu":
    os.environ["UBUNTU_MENUPROXY"] = "0" 
        
from MDANSE.App.GUI.DataController import DATA_CONTROLLER

import glob
import sys

directories = sorted([x[0] for x in os.walk(os.path.dirname(__file__))][1:])

for d in directories:
         
    for module in glob.glob(os.path.join(d,'*.py')):
                         
        moduleDir, moduleFile = os.path.split(module)
 
        if moduleFile == '__init__.py':
            continue
 
        moduleName, moduleExt = os.path.splitext(moduleFile)

        if moduleDir not in sys.path:        
            sys.path.append(moduleDir)
                  
        # Any error that may occur here has to be caught. In such case the module is skipped.    
        try:
            __import__(moduleName, locals(), globals())
        except:
            continue