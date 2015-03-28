import glob
import os

directories = [x[0] for x in os.walk(os.path.dirname(__file__))]

for d in directories:
    
    currentDir = os.getcwd()
 
    for module in glob.glob(os.path.join(d,'*.py')):
                         
        moduleDir, moduleFile = os.path.split(module)
 
        if moduleFile == '__init__.py':
            continue
 
        moduleName, moduleExt = os.path.splitext(moduleFile)
                  
        os.chdir(moduleDir)
                     
        # Any error that may occur here has to be caught. In such case the module is skipped.    
        try:
            __import__(moduleName, locals(), globals())
        except:
            continue
         
    os.chdir(currentDir)
    