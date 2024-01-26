# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/__init__.py
# @brief     Implements __init__
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************

"""A new part of the MDANSE code, created in November 2023,
the NeutronInstrument section will apply realistic constraints
to the simulation results to make them correspond to the
results expected from an experiment on a specific instrument.
As a starting point, three aspects of a neutron instrument
will be defined: incoming spectrum, detector coverage
and instrument resolution.

This will necessarily be a challenge to implement correctly,
since there are many different measurement techniques, all
of them resulting in a different resolution function.
An instrument database may be necessary to store realistic
settings for the MDANSE users. Lastly, different analysis
types will have to be modified to incorporate the instrument
effects in the calculation.
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
        tempmod = importlib.import_module("." + name, "MDANSE.NeutronInstruments")
    except ModuleNotFoundError:
        continue
    tempobject = getattr(tempmod, name)
    globdict[name] = tempobject
    del tempmod  # optionally delete the reference to the parent module
