#    This file is part of MDANSE.
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

import importlib
from pathlib import Path

current_path = Path(__file__).parent

modnames = (
    fname.stem for fname in current_path.glob("*.py") if fname.stem != "__init__"
)
globdict = globals()

for name in modnames:
    try:
        tempmod = importlib.import_module("." + name, "MDANSE.NeutronInstruments")
    except ModuleNotFoundError:
        continue
    tempobject = getattr(tempmod, name)
    globdict[name] = tempobject
    del tempmod  # optionally delete the reference to the parent module
