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

from typing import TypeAlias, TypeVar

import numpy as np
import numpy.typing as npt

FloatArray: TypeAlias = npt.NDArray[np.floating]
IntArray: TypeAlias = npt.NDArray[np.integer]
BoolArray: TypeAlias = npt.NDArray[np.bool_]
ByteArray: TypeAlias = npt.NDArray[np.uint8]
ComplexArray: TypeAlias = npt.NDArray[np.complexfloating]
NumArray = TypeVar("NumArray", FloatArray, ComplexArray)
