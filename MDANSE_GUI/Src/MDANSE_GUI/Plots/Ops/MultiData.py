#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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

from collections.abc import Iterable
from enum import auto

import numpy as np

from MDANSE.IO.IOUtils import UCEnum
from MDANSE.util_types import FloatArray
from MDANSE_GUI.Plots.Ops.Basic import Normalise
from MDANSE_GUI.Plots.Ops.Op import Op


@Op.register("globalnormalise")
class GlobalNormalise(Op):
    """Normalise values across the selected components.

    Parameters
    ----------
    mode : Normalisation
        Mode to normalise by:

        - MAX - Normalise s.t. the maximum value in array is 1.
        - ABSMAX - Normalise s.t. the absolute maximum value is 1.
        - SUM - Normalise s.t. the sum of the array is 1.
        - AVERAGE - Normalise by the mean.
    """

    STATS = ("scale_factor",)

    class Normalisation(UCEnum):
        MAX = auto()
        ABSMAX = auto()
        SUM = auto()
        AVERAGE = auto()

    def __init__(self, *args, mode: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.mode = mode

    @property
    def mode(self) -> Normalisation:
        return self._mode

    @mode.setter
    def mode(self, value: int | str | Normalisation):
        match value:
            case self.Normalisation():
                self._mode = value
            case str():
                self._mode = self.Normalisation[value]
            case int():
                self._mode = self.Normalisation(value)

    @property
    def params(self) -> dict[str, str]:
        return {"mode": self.mode.name}

    @classmethod
    def param_types(cls) -> dict[str, type]:
        return {"mode": cls.Normalisation}

    def pre_calculate(self, datasets: Iterable[FloatArray]):
        """Pre-compute some values from all targets before applying to data."""
        self.stats_calculate(datasets)

    def stats_calculate(self, datasets: Iterable[FloatArray]) -> None:
        """Pre-compute stats from all targets."""
        scale_factors = []
        for dataset in datasets:
            match self.mode:
                case self.Normalisation.AVERAGE:
                    scale_factors.append(np.nanmean(dataset))
                case self.Normalisation.MAX:
                    scale_factors.append(np.nanmax(dataset))
                case self.Normalisation.SUM:
                    scale_factors.append(np.sum(np.nan_to_num(dataset)))
                case self.Normalisation.ABSMAX:
                    scale_factors.append(np.nanmax(np.abs(dataset)))

        self.scale_factor = max(scale_factors)

    def apply_single(self, dataset: FloatArray) -> FloatArray:
        return dataset * (1 / self.scale_factor)

    @property
    def stats(self) -> dict[str, str]:
        return {"scale_factor": str(self.scale_factor)}
