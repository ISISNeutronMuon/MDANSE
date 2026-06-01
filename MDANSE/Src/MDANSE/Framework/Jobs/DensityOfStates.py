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
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    CorrelationWindow,
    FrameSelect,
    GroupingLevel,
    InstrumentResolution,
    InterpOrder,
    MDANSETrajectory,
    OutputFile,
    PartialCharge,
    Projection,
    RunningMode,
    Weights,
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

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        grouping="grouping_level",
        transmutation="atom_transmutation",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    instrument_resolution = InstrumentResolution(
        depends={"trajectory": "trajectory", "window": "frame_window"}
    )
    interpolation_order = InterpOrder(
        depends={"trajectory": "trajectory", "frames": "frames"}
    )
    projection = Projection()
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    weights = Weights(depends={"trajectory": "trajectory"}, default="atomic_weight")
    output_files = OutputFile()
    running_mode = RunningMode()

    PWR_NAME = "dos"
    PWR_UNITS = "au"
    MAIN_RESULTS = "dos/isotropic/"
