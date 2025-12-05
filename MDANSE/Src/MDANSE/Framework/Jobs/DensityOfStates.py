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

import collections
import copy

from MDANSE.Framework.Jobs.CartesianPowerSpectrum import CartesianPowerSpectrum
from MDANSE.Framework.Jobs.VelocityCorrelationFunction import (
    VelocityCorrelationFunction,
)


class DensityOfStates(CartesianPowerSpectrum, VelocityCorrelationFunction):
    """Calculate the vibrational density of states of the trajectory.

    The Density Of States describes the number of vibrations per unit frequency.
    In MDANSE the DOS calculation returns the Fourier transform (FT) of the weighted
    Velocity Correlation Function (vcf). With an atomic mass weighting scheme
    the MDANSE DOS result is proportional to the actual vibrational DOS.
    The partial DOS corresponds to selected sets of atoms or molecules.
    """

    label = "Density Of States"

    settings = copy.deepcopy(CartesianPowerSpectrum.settings)
    settings = list(settings.items())
    settings.insert(
        3,
        (
            "interpolation_order",
            (
                "InterpolationOrderConfigurator",
                {
                    "label": "velocities",
                    "dependencies": {"trajectory": "trajectory", "frames": "frames"},
                },
            ),
        ),
    )
    settings = collections.OrderedDict(settings)

    PWR_NAME = "dos"
    PWR_UNITS = "au"
    MAIN_RESULTS = "dos/isotropic/"
