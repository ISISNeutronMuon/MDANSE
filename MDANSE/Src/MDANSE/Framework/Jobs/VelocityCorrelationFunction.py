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

from MDANSE.Framework.Jobs.CartesianCorrelationFunction import (
    CartesianCorrelationFunction,
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

    settings = list(CartesianCorrelationFunction.settings.items())
    settings.insert(
        2,
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
    settings = dict(settings)

    def get_series(self, index):
        trajectory = self.trajectory
        atom_index = self.trajectory.atom_indices[index]

        if self.configuration["interpolation_order"]["value"] == 0:
            series = trajectory.read_configuration_trajectory(
                atom_index,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
                variable="velocities",
            )
        else:
            series = trajectory.read_atomic_trajectory(
                atom_index,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )

            order = self.configuration["interpolation_order"]["value"]
            for axis in range(3):
                series[:, axis] = differentiate(
                    series[:, axis],
                    order=order,
                    dt=self.configuration["frames"]["time_step"],
                )

        series = self.configuration["projection"]["projector"](series)
        return series
