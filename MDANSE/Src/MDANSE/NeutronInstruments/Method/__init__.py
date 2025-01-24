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

"""An implementation of the Strategy pattern, the Scattering Method
will take the instrument parameters, and calculate the weights and
range corrections according to the neutron scattering technique
specified by the user.

Parameters such as neutron spectrum and detector position matter
to all types of neutron scattering experiments, but will result
in a different set of equations depending on the type of an experiment
performed. Initially, the plan is to start with time-of-flight diffraction,
direct and indirect spectrometry."""

import importlib
from pathlib import Path

current_path = Path(__file__).parent

modnames = (
    fname.stem for fname in current_path.glob("*.py") if fname.stem != "__init__"
)
globdict = globals()

for name in modnames:
    try:
        tempmod = importlib.import_module(
            "." + name, "MDANSE.NeutronInstruments.Method"
        )
    except ModuleNotFoundError:
        continue
    tempobject = getattr(tempmod, name)
    globdict[name] = tempobject
    del tempmod  # optionally delete the reference to the parent module
