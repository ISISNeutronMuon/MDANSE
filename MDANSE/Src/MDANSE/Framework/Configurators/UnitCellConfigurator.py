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

from functools import singledispatchmethod

import numpy as np

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.Trajectory.FileTrajBase import TrajectoryFile
from MDANSE.util_types import FloatArray


@IConfigurator.register("UnitCellConfigurator")
class UnitCellConfigurator(IConfigurator):
    """Input a unit cell definition.

    This is normally used to introduce a cell definition to a trajectory,
    or to change the existing cell definition.
    """

    _default = np.eye(3), False
    label = "Unit cell"
    tooltip = "The definition of the simulation box dimensions."

    def __init__(self, name, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param valueType: the numeric type for the vector.
        :type valueType: int or float
        :param normalize: if True the vector will be normalized.
        :type normalize: bool
        :param notNull: if True, the vector must be non-null.
        :type notNull: bool
        :param dimension: the dimension of the vector.
        :type dimension: int
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        self["apply"] = False

    @singledispatchmethod
    def _get_cell(
        self, trajectory: Trajectory | TrajectoryFile
    ) -> tuple[FloatArray, FloatArray] | tuple[None, None]:
        raise Exception(f"Cannot handle trajectory of type {type(trajectory).__name__}")

    @_get_cell.register(Trajectory)
    def _(
        self, trajectory: Trajectory
    ) -> tuple[FloatArray, FloatArray] | tuple[None, None]:
        first = trajectory.unit_cell(0)
        last = trajectory.unit_cell(len(trajectory) - 1)

        if first is None or last is None:
            return None, None

        return first._unit_cell, last._unit_cell

    @_get_cell.register(TrajectoryFile)
    def _(
        self, trajectory: TrajectoryFile
    ) -> tuple[FloatArray, FloatArray] | tuple[None, None]:
        if trajectory.unit_cells_raw is None:
            return None, None
        return trajectory.unit_cells_raw[0], trajectory.unit_cells_raw[-1]

    def update_trajectory_information(self, traj_config: Trajectory | TrajectoryFile):

        first_cell, last_cell = self._get_cell(traj_config)

        has_valid_cell = not (
            first_cell is None
            or np.allclose(first_cell, 0.0)
            or np.allclose(last_cell, 0.0)
        )
        has_changing_cell = not np.allclose(first_cell, last_cell)

        if has_valid_cell and has_changing_cell:
            LOG.warning(
                "You will be overwriting a time-dependent unit cell definition with a FIXED unit cell!"
            )

        if not has_valid_cell:
            self.recommended_cell = (
                2.0 * np.eye(3) * np.linalg.norm(traj_config.max_span)
            )
            LOG.info(
                "Setting recommended cell to twice the maximum distance found in the trajectory."
            )
        else:
            self.recommended_cell = (first_cell + last_cell) / 2

        self.recommended_cell = self.recommended_cell.tolist()

    def configure(self, value: tuple[FloatArray, bool]) -> None:
        """Configure the unit cell as a 3x3 array.

        Parameters
        ----------
        value : tuple[FloatArray, bool]
            the vector components.
        """
        if not self.update_needed(value):
            return

        self._original_input = value
        self["apply"] = value[1]

        if self["apply"]:
            try:
                input_array = np.array(value[0], dtype=float)
            except Exception:
                self.error_status = (
                    "Could not convert the inputs into a floating point array."
                )
                return

            if input_array.shape != (3, 3):
                self.error_status = "Input shape must be 3x3."
                return

            self["value_raw"] = input_array
        else:
            self["value_raw"] = np.eye(3)

        self["value"] = UnitCell(self["value_raw"])
        self.error_status = "OK"
