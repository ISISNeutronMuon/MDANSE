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

"""The greatest challenge so far in the realistic neutron instrument
implementation, the resolution calculation, will be different for
different experiment methods. Knowledge of instrument parameters
will be required.

Typically, for an Inelastic Neutron Scattering instrument, the
resolution will depend on the source-sample and sample-detector
distances, the chopper speeds, and the Ei/Ef ratio."""

from __future__ import annotations

from .IdealResolution import IdealResolution as IdealResolution
from .Resolution import Resolution as Resolution
