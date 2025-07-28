#    This file is part of MDANSE_GUI.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import annotations

import glob
import importlib
import os

from MDANSE.MLogging import LOG

current_path, _ = os.path.split(__file__)

modnames = []
fnames = glob.glob(current_path + "/*.py")
for fname in fnames:
    _, newname = os.path.split(fname)
    newname = newname.split(".py")[0]
    modnames.append(newname)
globdict = globals()

for name in modnames:
    if name in ["__init__", "PlotterTemplate"]:
        continue
    try:
        tempmod = importlib.import_module("." + name, "MDANSE_GUI.Tabs.Plotters")
    except ModuleNotFoundError:
        LOG.error(f"Could not find {name} in MDANSE_GUI.Tabs.Plotters")
    else:
        tempobject = getattr(tempmod, name)
        globdict[name] = tempobject
        del tempmod  # optionally delete the reference to the parent module
