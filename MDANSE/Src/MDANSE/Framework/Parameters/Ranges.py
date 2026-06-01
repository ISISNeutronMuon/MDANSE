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

from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from MDANSE.Framework.Parameters.BaseTypes import NumericRange, Range
from MDANSE.Framework.Parameters.Parameters import ConfigError
from MDANSE.Framework.Parameters.UtilTypes import Depends, DescID, PredictionResult

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from MDANSE.MolecularDynamics.Trajectory import Trajectory


class HistogramInfo:
    def __init__(self, bins: NumericRange):
        if isinstance(bins, HistogramInfo):
            bins = bins.binning
        self.binning = bins

    def __len__(self) -> int:
        return len(self.binning)

    @property
    def start(self) -> float:
        return self.binning.start

    @property
    def stop(self) -> float:
        return self.binning.stop

    @property
    def step(self) -> float:
        return self.binning.step

    @property
    def bins(self) -> npt.NDArray[np.floating]:
        return np.array(list(self.binning), dtype=np.float64)

    @property
    def mid_points(self) -> npt.NDArray[np.floating]:
        return (self.bins[1:] + self.bins[:-1]) / 2


class QShellRange(Range[float]):
    """Addition of output predictor."""

    def preview_output_axis(self, value, raw) -> Iterator[PredictionResult]:
        yield PredictionResult("Q Values", list(value), "nm")


class RangeCellCutoff(Range[float, HistogramInfo]):
    """Range of interatomic distances for a histogram.

    It does not allow distances large enough to include
    the periodic image of any atom in the system.
    """

    def __init__(self, *args, max_value: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_value = max_value

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory")}

    def validate(
        self,
        value: int | Sequence | dict | range,
        deps: Depends,
        /,
    ) -> HistogramInfo:
        """Configure the distance histogram cutoff configurator.

        Parameters
        ----------
        value : tuple
            A tuple of the range parameters.
        """
        value = super().validate(value, deps)

        if self._max_value:
            try:
                self.validate_range(value.stop, self.get_ranges(deps))
            except ConfigError:
                raise ConfigError(
                    "The cutoff distance goes into the simulation box periodic images."
                ) from None

        return HistogramInfo(value)

    def preview_output_axis(self, value, raw) -> Iterator[PredictionResult]:
        yield PredictionResult("R Values", value.binning, "nm")

    def get_ranges(self, deps: Depends):
        return (0, round(self.get_largest_cutoff(deps["trajectory"]), 2))

    @staticmethod
    def get_largest_cutoff(trajectory: Trajectory) -> float:
        """Get the largest cutoff value for the given trajectories
        unit cells.

        Returns
        -------
        float
            The maximum cutoff for the distance histogram job.
        """
        try:
            trajectory_array = np.array(
                [
                    trajectory.unit_cell(frame)._unit_cell
                    for frame in range(len(trajectory))
                ]
            )
        except Exception:
            return np.linalg.norm(trajectory.min_span)

        if np.allclose(trajectory_array, 0.0):
            return np.linalg.norm(trajectory.min_span)

        # calculated the radius of the largest sphere that can
        # fit into the unit cell
        min_d = np.min(trajectory_array, axis=0)
        vec_a, vec_b, vec_c = min_d

        cross_bc = np.cross(vec_b, vec_c)
        cross_ca = np.cross(vec_c, vec_a)
        cross_ab = np.cross(vec_a, vec_b)

        if (
            np.allclose(cross_bc, 0.0)
            or np.allclose(cross_ca, 0.0)
            or np.allclose(cross_ab, 0.0)
        ):
            raise ValueError("Trajectory contains invalid unit cell.")

        h_1 = abs(np.dot(vec_a, cross_bc)) / np.linalg.norm(cross_bc)
        h_2 = abs(np.dot(vec_b, cross_ca)) / np.linalg.norm(cross_ca)
        h_3 = abs(np.dot(vec_c, cross_ab)) / np.linalg.norm(cross_ab)

        return 0.5 * min(h_1, h_2, h_3)
