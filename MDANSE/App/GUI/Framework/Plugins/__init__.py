import glob
import os

from MDANSE import REGISTRY
from MDANSE.App.GUI.Framework.Plugins.DataPlugin import DataPlugin 
from MDANSE.App.GUI.Framework.Plugins.JobPlugin import JobPlugin

for job in REGISTRY["job"].values():

    if not hasattr(job, "type"):
        continue
            
    attrs = {"type"      : job.type,
             "ancestor"  : getattr(job,"ancestor",""),
             "category"  : ('Analysis',) + getattr(job, "category", ("Miscellaneous",)),
             "label"     : getattr(job, "label", job.__name__)}
            
    kls = type("%sPlugin" % job.__name__, (JobPlugin,), attrs)

for data in REGISTRY["input_data"].values():

    if not hasattr(data, "type"):
        continue

    attrs = {"type"     : data.type, 
             "label"    : " ".join("".split("_")).capitalize(),
             "ancestor" : ""}
    kls = type("%sPlugin" % data.__name__, (DataPlugin,), attrs)