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
from __future__ import annotations

from MDANSE.Framework.Jobs.CartesianPowerSpectrum import CartesianPowerSpectrum
from MDANSE.Framework.Jobs.PositionCorrelationFunction import (
    PositionCorrelationFunction,
)


class PositionPowerSpectrum(CartesianPowerSpectrum, PositionCorrelationFunction):
    """Calculates the position power spectrum.

    Power spectrum (using Fast Fourier Transform) of atomic trajectories calculated
    from the Positional correlation Function (PCF). The calculation result
    is similar to the density of states, which is calculated from the velocity
    correlation function. In fact, PPS and DOS may show the same features
    in systems where position and velocity are strongly correlated (i.e. solids).

    This calculation is used by TrajectoryFilter to create a preview of the spectrum,
    so that a desired range of atomic vibrational modes can be isolated.
    """

    label = "Position Power Spectrum"
    PWR_NAME = "pps"
    PWR_UNITS = "au"
    MAIN_RESULTS = "pps/isotropic/"
