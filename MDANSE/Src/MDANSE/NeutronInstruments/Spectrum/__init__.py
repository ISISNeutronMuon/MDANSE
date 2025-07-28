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

"""The number of neutrons arriving at the sample in a unit of time
will be, necessarily, wavelength-dependent. While on a direct TOF
instrument this will affect only the absolute intensity of the signal,
in the case of polychromatic neutron instruments this will introduce
an additional weight factor scaling the relative contributions of
different neutron wavelength to the total observed scattering signal.
"""

from __future__ import annotations

from .FlatSpectrum import FlatSpectrum as FlatSpectrum
from .Spectrum import Spectrum as Spectrum
