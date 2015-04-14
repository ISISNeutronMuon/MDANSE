import os
import platform

# Hack for the (in)famous "(python:865): LIBDBUSMENU-GLIB-WARNING **: Trying to remove a child that doesn't believe we're it's parent."
if platform.dist()[0].lower() == "ubuntu":
    os.environ["UBUNTU_MENUPROXY"] = "0" 
        
from MDANSE.App.GUI.DataController import DATA_CONTROLLER

from MDANSE import REGISTRY

directories = sorted([x[0] for x in os.walk(os.path.join(os.path.dirname(__file__),'Framework'))][1:])

for d in directories:
    REGISTRY.update_registry(d)
