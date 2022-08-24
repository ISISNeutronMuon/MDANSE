import os
import subprocess
from AppKit import NSBundle

path = NSBundle.mainBundle().executablePath
script_path = NSBundle.mainBundle().resourcePath
p = subprocess.check_call('{} {}'.format(os.path.join(path, 'python'), os.path.join(script_path, 'mdanse_gui')),
                          shell=True)
