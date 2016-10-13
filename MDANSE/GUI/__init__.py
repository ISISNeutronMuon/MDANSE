import glob
import os
import platform

from wx.lib.pubsub.pub import Publisher

PUBLISHER = Publisher()

# Hack for the (in)famous "(python:865): LIBDBUSMENU-GLIB-WARNING **: Trying to remove a child that doesn't believe we're it's parent."
if platform.dist()[0].lower() == "ubuntu":
    os.environ["UBUNTU_MENUPROXY"] = "0" 
        
from MDANSE import PLATFORM, REGISTRY
from MDANSE.GUI.Plugins.DataPlugin import DataPlugin 
from MDANSE.GUI.Plugins.JobPlugin import JobPlugin

directories = sorted([x[0] for x in os.walk(os.path.dirname(__file__))][1:])

macrosDir = PLATFORM.macros_directory()
directories.insert(0,macrosDir)
directories.extend(sorted([x[0] for x in os.walk(macrosDir)][1:]))

for d in directories:
    REGISTRY.update_registry(d)

for job in REGISTRY["job"].values():

    if not hasattr(job, "type"):
        continue
                    
    attrs = {"type"      : job.type,
             "ancestor"  : getattr(job,'ancestor',job.ancestor),
             "category"  : getattr(job, "category", ("Miscellaneous",)),
             "label"     : getattr(job, "label", job.__name__)}
            
    kls = type("%sPlugin" % job.__name__, (JobPlugin,), attrs)

for data in REGISTRY["input_data"].values():

    if not hasattr(data, "type"):
        continue

    attrs = {"type"     : data.type, 
             "label"    : " ".join("".split("_")).capitalize(),
             "ancestor" : ['empty_data']}
    kls = type("%sPlugin" % data.__name__, (DataPlugin,), attrs)