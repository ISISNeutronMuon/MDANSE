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

from math import isclose
from typing import TYPE_CHECKING

from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QDoubleSpinBox

if TYPE_CHECKING:
    from collections.abc import Callable


class SnapSpinBox(QDoubleSpinBox):
    """Spinbox which forcibly snaps to its step."""

    def __init__(
        self,
        *args,
        minmax: tuple[float, float] | None = None,
        step: float | None = None,
        decimal: int | None = None,
        suffix: str | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if minmax is not None:
            self.setRange(*minmax)
        if step is not None:
            self.setSingleStep(step)
        if decimal is not None:
            self.setDecimals(decimal)
        if suffix is not None:
            self.setSuffix(suffix)

    def nearest(self, val) -> float:
        return self.singleStep() * round(val / self.singleStep())

    def validate(
        self, input: str | None, pos: int
    ) -> tuple[QValidator.State, str, int]:
        valid, value, pos = super().validate(input, pos)

        if valid is QValidator.State.Invalid or not value:
            return valid, value, pos

        fval = float(value.removesuffix(self.suffix()))
        valid = (
            valid
            if isclose(fval, self.nearest(fval), abs_tol=10 ** (-self.decimals()))
            else QValidator.State.Intermediate
        )

        return valid, value, pos

    def fixup(self, value: str) -> str:
        value = super().fixup(value)
        snapped = self.nearest(float(value.removesuffix(self.suffix())))
        return super().fixup(str(snapped))


class ConstrainedSnapSpinBox(SnapSpinBox):
    """SnapSpinBox with extra functional constraint."""

    def __init__(
        self, *args, constraint: Callable[[float], bool] | None = None, **kwargs
    ):
        self.constraint = constraint
        super().__init__(*args, **kwargs)

    def validate(
        self, input: str | None, pos: int
    ) -> tuple[QValidator.State, str, int]:
        valid, value, pos = super().validate(input, pos)

        if valid is QValidator.State.Invalid or self.constraint is None:
            return valid, value, pos

        valid = (
            valid
            if self.constraint(float(value.removesuffix(self.suffix())))
            else QValidator.State.Intermediate
        )

        return valid, value, pos
