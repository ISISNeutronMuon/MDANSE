import os
import platform

# Hack for the (in)famous "(python:865): LIBDBUSMENU-GLIB-WARNING **: Trying to remove a child that doesn't believe we're it's parent."
if platform.dist()[0].lower() == "ubuntu":
    os.environ["UBUNTU_MENUPROXY"] = "0" 
