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

from enum import auto
from typing import Any, SupportsFloat

import numpy as np

from MDANSE.IO.IOUtils import UCEnum
from MDANSE.util_types import FloatArray
from MDANSE_GUI.Plots.ops.op import Op


@Op.register("abs")
class Abs(Op):
    def apply_single(self, dataset: FloatArray) -> FloatArray:
        return np.abs(dataset)

    @property
    def params(self) -> dict[str, Any]:
        return {}

    @classmethod
    def param_types(cls) -> dict[str, type]:
        return {}


@Op.register("ln")
class Ln(Op):
    def apply_single(self, dataset: FloatArray) -> FloatArray:
        return np.log(dataset)

    @property
    def params(self) -> dict[str, Any]:
        return {}

    @classmethod
    def param_types(cls) -> dict[str, type]:
        return {}


@Op.register("exp")
class Exp(Op):
    def apply_single(self, dataset: FloatArray) -> FloatArray:
        return np.exp(dataset)

    @property
    def params(self) -> dict[str, Any]:
        return {}

    @classmethod
    def param_types(cls) -> dict[str, type]:
        return {}


@Op.register("shift")
class Shift(Op):
    def __init__(self, *args, amount: float = 0.0, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.amount = amount

    def apply_single(self, dataset: FloatArray) -> FloatArray:
        return dataset + self.amount

    @property
    def params(self) -> dict[str, Any]:
        return {"amount": self.amount}

    @classmethod
    def param_types(self) -> dict[str, type]:
        return {"amount": float}


@Op.register("pow")
class Pow(Op):
    def __init__(self, *args, exponent: float = 0.0, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.exponent = exponent

    def apply_single(self, dataset: FloatArray) -> FloatArray:
        return dataset**self.exponent

    @property
    def params(self) -> dict[str, Any]:
        return {"exponent": self.exponent}

    @classmethod
    def param_types(self) -> dict[str, type]:
        return {"exponent": float}


@Op.register("rescale")
class Rescale(Op):
    def __init__(self, *args, amount: float = 0.0, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.amount = amount

    def apply_single(self, dataset: FloatArray) -> FloatArray:
        return dataset * self.amount

    @property
    def params(self) -> dict[str, Any]:
        return {"amount": self.amount}

    @classmethod
    def param_types(self) -> dict[str, type]:
        return {"amount": float}


@Op.register("scaletorange")
class ScaleToRange(Op):
    def __init__(self, *args, min_val: float, max_val: float, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.range = min_val, max_val

    @property
    def params(self) -> dict[str, float]:
        return {
            "min_val": self.min_val,
            "max_val": self.max_val,
        }

    @classmethod
    def param_types(cls) -> dict[str, type]:
        return {
            "min_val": float,
            "max_val": float,
        }

    @property
    def min_val(self) -> float:
        return self._min_val

    @min_val.setter
    def min_val(self, value: SupportsFloat) -> None:
        value = float(value)
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"Min val ({value}) greater than max val ({self.max_val})")
        self._min_val = value

    @property
    def max_val(self) -> float:
        return self._max_val

    @max_val.setter
    def max_val(self, value: SupportsFloat) -> None:
        value = float(value)
        if self.max_val is not None and value < self.min_val:
            raise ValueError(f"Max val ({value}) less than min val ({self.min_val})")
        self._max_val = value

    @property
    def range(self) -> float:
        return self.max_val - self.min_val

    @range.setter
    def range(self, value: tuple[SupportsFloat, SupportsFloat]) -> None:
        self._min_val, self._max_val = sorted(map(float, value))

    def apply_single(self, dataset: FloatArray) -> FloatArray:
        ds_max = np.max(dataset)
        ds_min = np.min(dataset)

        return ((dataset - ds_min) / (ds_max - ds_min)) * self.range + self.min_val


@Op.register("truncate")
class Truncate(Op):
    class Truncation(UCEnum):
        VALUE = auto()
        PERCENT = auto()

    def __init__(self, *args, min_val: float, max_val: float, mode: Truncation | str | int, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.range = min_val, max_val
        self.mode = mode

    @property
    def mode(self) -> Truncation:
        return self._mode

    @mode.setter
    def mode(self, value: int | str | Truncation):
        match value:
            case self.Truncation():
                self._mode = value
            case str():
                self._mode = self.Truncation[value]
            case int():
                self._mode = self.Truncation(value)

    @property
    def params(self) -> dict[str, float | str]:
        return {
            "mode": self.mode.name,
            "min_val": self.min_val,
            "max_val": self.max_val,
        }

    @classmethod
    def param_types(cls) -> dict[str, type]:
        return {
            "mode": cls.Truncation,
            "min_val": float,
            "max_val": float,
        }

    @property
    def min_val(self) -> float:
        return self._min_val

    @min_val.setter
    def min_val(self, value: SupportsFloat) -> None:
        value = float(value)
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"Min val ({value}) greater than max val ({self.max_val})")
        self._min_val = value

    @property
    def max_val(self) -> float:
        return self._max_val

    @max_val.setter
    def max_val(self, value: SupportsFloat) -> None:
        value = float(value)
        if self.max_val is not None and value < self.min_val:
            raise ValueError(f"Max val ({value}) less than min val ({self.min_val})")
        self._max_val = value

    @property
    def range(self) -> float:
        return self.max_val - self.min_val

    @range.setter
    def range(self, value: tuple[SupportsFloat, SupportsFloat]) -> None:
        self._min_val, self._max_val = sorted(map(float, value))

    def apply_single(self, dataset: FloatArray) -> FloatArray:

        abs_ds = np.abs(dataset)
        match self.mode:
            case self.Truncation.PERCENT:
                maxi = self.max_val * np.nanmax(abs_ds) / 100
                mini = self.min_val * np.nanmax(abs_ds) / 100
            case self.Truncation.VALUE:
                maxi = self.max_val
                mini = self.min_val

        out = dataset.copy()
        out[(abs_ds < mini) | (abs_ds > maxi)] = np.nan
        return out


@Op.register("normalise")
class Normalise(Op):

    class Normalisation(UCEnum):
        AVERAGE = auto()
        MAX = auto()
        SUM = auto()
        ABSMAX = auto()

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

    def apply_single(self, dataset: FloatArray) -> FloatArray:
        match self.mode:
            case self.Normalisation.AVERAGE:
                scale_factor = np.nanmean(dataset)
            case self.Normalisation.MAX:
                scale_factor = np.nanmax(dataset)
            case self.Normalisation.SUM:
                scale_factor = np.sum(np.nan_to_num(dataset))
            case self.Normalisation.ABSMAX:
                scale_factor = np.nanmax(np.abs(dataset))

        return dataset * (1 / scale_factor)
