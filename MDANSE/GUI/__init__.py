import glob
import os
import platform

from MDANSE.Externals.pubsub import pub as PUBLISHER

# Hack for the (in)famous "(python:865): LIBDBUSMENU-GLIB-WARNING **: Trying to remove a child that doesn't believe we're it's parent."
if platform.dist()[0].lower() == "ubuntu":
    os.environ["UBUNTU_MENUPROXY"] = "0" 
        
from MDANSE import PLATFORM, REGISTRY
from MDANSE.GUI.Plugins.DataPlugin import DataPlugin 
from MDANSE.GUI.Plugins.JobPlugin import JobPlugin

from MDANSE.GUI.Handlers import *
from MDANSE.GUI.Plugins import *
from MDANSE.GUI.Widgets import *

macrosDirectories = sorted([x[0] for x in os.walk(PLATFORM.macros_directory())][0:])
 
for d in macrosDirectories:
    REGISTRY.update(d)

for job in REGISTRY["job"].values():

    if not hasattr(job, "_type"):
        continue
                    
    attrs = {"_type"     : job._type,
             "ancestor"  : getattr(job,'ancestor',job.ancestor),
             "category"  : getattr(job, "category", ("Miscellaneous",)),
             "label"     : getattr(job, "label", job.__name__)}
            
    kls = type("%sPlugin" % job.__name__, (JobPlugin,), attrs)
    REGISTRY[job._type] = kls

for data in REGISTRY["input_data"].values():

    if not hasattr(data, "_type"):
        continue

    attrs = {"_type"    : data._type, 
             "label"    : " ".join("".split("_")).capitalize(),
             "ancestor" : ['empty_data']}
    kls = type("%sPlugin" % data.__name__, (DataPlugin,), attrs)
    REGISTRY[data._type] = kls