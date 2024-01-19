# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/Coverage/__init__.py
# @brief     Implements __init__
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************

"""Instrument coverage will be expressed as angular coverage of
detectors. By specifying the angle coverage of detector panels,
we can limit the range of accessible Q vectors to those that
a specific instrument can access.
"""

import glob
import importlib
import os

current_path, _ = os.path.split(__file__)

modnames = []
fnames = glob.glob(current_path + "/*.py")
for fname in fnames:
    _, newname = os.path.split(fname)
    newname = newname.split(".py")[0]
    modnames.append(newname)
globdict = globals()

for name in modnames:
    if name in ["__init__"]:
        continue
    try:
        tempmod = importlib.import_module(
            "." + name, "MDANSE.NeutronInstruments.Coverage"
        )
    except ModuleNotFoundError:
        continue
    tempobject = getattr(tempmod, name)
    globdict[name] = tempobject
    del tempmod  # optionally delete the reference to the parent module