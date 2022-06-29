# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import glob
import os

import distro

import wx

from MDANSE import PLATFORM
from MDANSE.Externals.pubsub import pub as PUBLISHER

# Hack for the (in)famous "(python:865): LIBDBUSMENU-GLIB-WARNING **: Trying to remove a child that doesn't believe we're it's parent."
try:
  if distro.linux_distribution()[0].lower() == "ubuntu":
    os.environ["UBUNTU_MENUPROXY"] = "0" 
except:
  pass

if PLATFORM.name == "macos":
    wx.SystemOptions.SetOption("osx.openfiledialog.always-show-types","1")
        
from MDANSE import REGISTRY
from MDANSE.GUI.Plugins.DataPlugin import DataPlugin 
from MDANSE.GUI.Plugins.JobPlugin import JobPlugin

REGISTRY.update(os.path.join(os.path.dirname(__file__),"Handlers"))
REGISTRY.update(os.path.join(os.path.dirname(__file__),"Plugins"))
REGISTRY.update(os.path.join(os.path.dirname(__file__),"Widgets"))

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
