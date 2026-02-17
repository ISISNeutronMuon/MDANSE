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

from collections.abc import Sequence

import numpy as np

from MDANSE.Framework.Configurators.FloatConfigurator import FloatConfigurator
from MDANSE.MolecularDynamics.Trajectory import Trajectory

from .IConfigurator import PredictionSettings


class GridStepConfigurator(FloatConfigurator):
    """Configurator to manage a finite element grid within the unit cell.

    This configurator provides extra information about a grid in a
    trajectory's unit cell.

    It can also read a primary cell-vector along which the spacing is defined
    which is specified in the optional `axis` dependency
    (an :class:`AxisSelectionConfigurator` instance).

    If any frame does not have a unit cell, the maximum span of the atoms is
    used, otherwise the average unit cell is used.

    The input value specifies the grid spacing in `nm`.

    If `axis` is present, information about the prediction is stored in `grid`
    and is a single range along the primary axis.

    If `axis` is not present, information about the prediction is stored in the keys:

    - `a-direction grid`
    - `b-direction grid`
    - `c-direction grid`
    """

    label = "Size of the grid step"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["grid"] = []
        self.prediction = PredictionSettings(
            key="grid", label="Real space bin centres", unit="nm"
        )
        self._avg_cell = None
        self._last_frames = []

    def new_frames(self) -> Sequence[float] | None:
        new_frames = self.configurable[self.dependencies["frames"]]["value"]
        if len(new_frames) != len(self._last_frames) or not np.allclose(
            new_frames, self._last_frames
        ):
            self._last_frames = new_frames
            return new_frames
        return None

    @property
    def average_unit_cell(self):
        frames = self.new_frames()
        if frames is not None:
            self._avg_cell = None
        if self._avg_cell is not None:
            return self._avg_cell
        trajectory: Trajectory = self.configurable[self.dependencies["trajectory"]][
            "instance"
        ]
        if any(trajectory.unit_cell(frame) is None for frame in frames):
            self._avg_cell = trajectory.max_span
        else:
            self._avg_cell = np.array(
                [trajectory.unit_cell(frame)._unit_cell for frame in frames]
            ).mean(axis=0)
        return self._avg_cell

    def configure(self, value):
        super().configure(value)

        trajectory: Trajectory = self.configurable[self.dependencies["trajectory"]][
            "instance"
        ]
        unit_cell = self.average_unit_cell
        if unit_cell is None:
            axes = trajectory.max_span
        else:
            axes = np.linalg.norm(unit_cell, axis=0)
        if "axis" in self.dependencies:
            axis_index = self.configurable[self.dependencies["axis"]]["index"]
            axis_length = axes[axis_index]
            temp_array = np.arange(
                0.0, axis_length - 0.1 * self["value"], self["value"]
            )
            self["grid"] = temp_array + 0.5 * self["value"]
            return
        self.prediction_keys = [
            "a-direction grid",
            "b-direction grid",
            "c-direction grid",
        ]
        self["grid"] = []
        temp = [
            np.arange(0.0, axes[index] - 0.1 * self["value"], self["value"])
            + 0.5 * self["value"]
            for index in range(3)
        ]
        for arr_index, temp_array in enumerate(temp):
            self[self.prediction_keys[arr_index]] = temp_array
