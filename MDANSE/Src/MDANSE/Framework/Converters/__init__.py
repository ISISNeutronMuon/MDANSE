# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Converters/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
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
        tempmod = importlib.import_module("." + name, "MDANSE.Framework.Converters")
    except ModuleNotFoundError:
        print(f"Could not find {name} in MDANSE.Framework.Converters")
    tempobject = getattr(tempmod, name)
    globdict[name] = tempobject
    del tempmod  # optionally delete the reference to the parent module