import glob
import os
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
         
