import glob
import os

for module in glob.glob(os.path.join(os.path.dirname(__file__),'*.py')):

    module = os.path.basename(module)
    
    if module == '__init__.py':
        continue

    module = os.path.splitext(module)[0]

    # Any error that may occur here has to be caught. In such case the module is skipped.    
    try:
        __import__(module, locals(), globals())
    except:
        continue

