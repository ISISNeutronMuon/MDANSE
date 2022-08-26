import os
import subprocess

contents = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join(contents, 'MacOS'))

subprocess.check_call('./launch_mdanse', shell=True)
