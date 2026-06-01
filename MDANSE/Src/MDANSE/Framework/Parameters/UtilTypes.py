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

from collections.abc import Container, Iterable
from typing import TYPE_CHECKING, NamedTuple, NewType

import numpy as np
import numpy.typing as npt
from typing_extensions import TypedDict, TypeVar

if TYPE_CHECKING:
    from MDANSE.Core.SubclassFactory import SubclassFactory
    from MDANSE.Framework.Parameters.Frames import Frames, FrameWindow
    from MDANSE.Framework.Parameters.Parameters import ConfigureDescriptor
    from MDANSE.Framework.Projectors.IProjector import IProjector
    from MDANSE.Framework.QVectors.IQVectors import IQVectors
    from MDANSE.Mathematics.Signal import Filter as SFilter
    from MDANSE.MolecularDynamics.Trajectory import Trajectory

P = TypeVar("P")
T = TypeVar("T")
CB = TypeVar("CB", default=T)
Num = TypeVar("Num", int, float)
K = TypeVar("K")
V = TypeVar("V")
CD = TypeVar("CD", bound="ConfigureDescriptor")
SC = TypeVar("SC", bound="SubclassFactory")

SupportsDict = Iterable[tuple[K, V]] | dict[K, V]
DescID = NewType("DescID", str)


class EmptyDict(TypedDict, closed=True): ...


class Depends(TypedDict, total=False, extra_items=object):
    trajectory: Trajectory
    frames: Frames
    window: FrameWindow
    selection: Container[int]
    transmutation: dict[int, str]
    generator: IQVectors
    projector: IProjector
    filter: SFilter


class PredictionResult(NamedTuple):
    """Strings used for showing the predicted output range in the GUI.

    :label: An explanation for the user of what physical property the numbers represent.
    :data: Data representing prediction if numeric otherwise attribute containing data.
    :unit: The internal unit of MDANSE of the numerical array. Used for converting to GUI units.
    """

    label: str
    data: Iterable[float] | str
    unit: str = "none"
