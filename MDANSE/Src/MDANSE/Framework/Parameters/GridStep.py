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

from typing import TYPE_CHECKING, ClassVar, Final, SupportsFloat, overload

import numpy as np

from MDANSE.Framework.Parameters.BaseTypes import Float
from MDANSE.Framework.Parameters.Parameters import ConfigError
from MDANSE.Framework.Parameters.UtilTypes import Depends, DescID, PredictionResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from MDANSE.Framework.Parameters.Frames import Frames


class GridStep(Float):
    """Configurator to manage a finite element grid within the unit cell.

    This configurator provides extra information about a grid in a
    trajectory's unit cell.

    It can also read a primary cell-vector along which the spacing is defined
    which is specified in the optional `axis` dependency
    (an :class:`ModecularAxis` instance).

    If any frame does not have a unit cell, the maximum span of the atoms is
    used, otherwise the average unit cell is used.

    The input value specifies the grid spacing in `nm`.
    """

    PREDICTOR_FORMAT: ClassVar[str] = "{}-direction grid"
    default_label = "Size of the grid step"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.grid = []
        self._avg_cell = None
        self._last_frames = []

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory"), DescID("frames")}

    def new_frames(self, deps: Depends) -> Frames | None:
        new_frames = deps["frames"]
        if new_frames != self._last_frames:
            self._last_frames = new_frames
            return new_frames
        return None

    def average_unit_cell(self, deps: Depends):
        frames = self.new_frames(deps)
        if frames is not None:
            self._avg_cell = None

        if self._avg_cell is not None:
            return self._avg_cell

        trajectory = deps["trajectory"]
        if any(trajectory.unit_cell(frame.ind) is None for frame in frames):
            self._avg_cell = trajectory.max_span
        else:
            self._avg_cell = np.array(
                [trajectory.unit_cell(frame.ind)._unit_cell for frame in frames]
            ).mean(axis=0)
        return self._avg_cell

    @overload
    def validate(self, value: None, deps: Depends, /) -> None: ...
    @overload
    def validate(self, value: SupportsFloat, deps: Depends, /) -> float: ...
    def validate(self, value, deps):
        value = super().validate(value, deps)

        unit_cell = self.average_unit_cell(deps)

        if unit_cell is None:
            axes = deps["trajectory"].max_span
        else:
            axes = np.linalg.norm(unit_cell, axis=0)

        def get_grid(axis_length):
            return np.arange(0.0, axis_length - 0.1 * value, value) + 0.5 * value

        if "axis" in deps:
            axis_index = "abc".index(deps["axis"])
            axis_length = axes[axis_index]
            self.prediction = {
                self.PREDICTOR_FORMAT.format(deps["axis"]): get_grid(axis_length)
            }
        else:
            self.prediction = {
                self.PREDICTOR_FORMAT.format(key): get_grid(axis)
                for key, axis in zip("abc", axes, strict=True)
            }

        return value

    def preview_output_axis(self, value, raw) -> Iterator[PredictionResult]:
        for key, val in self.prediction.items():
            yield PredictionResult(key, val, "nm")
