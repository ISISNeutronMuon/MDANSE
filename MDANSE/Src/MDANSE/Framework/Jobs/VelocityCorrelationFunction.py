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

from MDANSE.Framework.Jobs.CartesianCorrelationFunction import (
    CartesianCorrelationFunction,
)
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    CorrelationWindow,
    FrameSelect,
    GroupingLevel,
    InterpOrder,
    MDANSETrajectory,
    OutputFile,
    PartialCharge,
    Projection,
    RunningMode,
    Weights,
)
from MDANSE.Mathematics.Signal import differentiate


class VelocityCorrelationFunction(CartesianCorrelationFunction):
    r"""Calculates the velocity correlation function of the selected atoms.

    The Velocity Correlation Function (VCF) is a property describing the dynamics
    of a molecular system. It reveals the underlying nature of the forces acting on
    the system. Its Fourier Transform gives the cartesian density of states for a set
    of atoms.
    """

    enabled = True
    label = "Velocity Correlation Function"
    CF_NAME = "vcf"
    CF_UNITS = "nm2/ps2"
    MAIN_RESULTS = "vcf/isotropic/"

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        grouping="grouping_level",
        transmutation="atom_transmutation",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    interpolation_order = InterpOrder(
        depends={"trajectory": "trajectory", "frames": "frames"},
        label="velocities",
    )
    projection = Projection()
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    weights = Weights(depends={"trajectory": "trajectory"})
    output_files = OutputFile()
    running_mode = RunningMode()

    def get_series(self, index):
        trajectory = self.trajectory
        atom_index = self.trajectory.atom_indices[index]

        if self.interpolation_order == 0:
            series = trajectory.read_configuration_trajectory(
                atom_index,
                first=self.frames.index_start,
                last=self.frames.index_stop + 1,
                step=self.frames.index_step,
                variable="velocities",
            )
        else:
            series = trajectory.read_atomic_trajectory(
                atom_index,
                first=self.frames.index_start,
                last=self.frames.index_stop + 1,
                step=self.frames.index_step,
            )

            for axis in range(3):
                series[:, axis] = differentiate(
                    series[:, axis],
                    order=self.interpolation_order,
                    dt=self.frames.time_step,
                )

        series = self.projection.projector(series)
        return series
