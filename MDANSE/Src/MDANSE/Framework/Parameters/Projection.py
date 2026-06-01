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

from enum import Enum, auto
from functools import singledispatchmethod
from typing import TYPE_CHECKING

from MDANSE.Framework.Parameters.BaseTypes import Vector
from MDANSE.Framework.Parameters.Choices import SingleChoice
from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    Configurable,
    CustomConfig,
)
from MDANSE.Framework.Projectors.IProjector import IProjector
from MDANSE.IO.IOUtils import UCEnum
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt


class ProjType(UCEnum):
    NULL = auto()
    AXIAL = auto()
    PLANAR = auto()

    NULLPROJECTOR = NULL
    AXIALPROJECTOR = AXIAL
    PLANARPROJECTOR = PLANAR


class Projection(CustomConfig):
    proj_type = SingleChoice(choices=ProjType, default=ProjType.NULL)
    axis = Vector[float | None](
        optional=True,
        non_zero=True,
        normalise=True,
        default=None,
    )

    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    @property
    def projector(self) -> IProjector:
        if not self.check_status():
            LOG.warning(
                f"Projector ({self.proj_type.name}) requested, but no axis defined, returning NullProjector"
            )
            return IProjector.create("NullProjector")

        proj = IProjector.create(self.proj_type.name.title() + "Projector")

        if self.proj_type is not ProjType.NULL:
            proj.set_axis(self.axis)

        return proj

    @projector.setter
    def projector(
        self,
        value: IProjector
        | tuple[ProjType | str, npt.NDArray[np.floating] | None]
        | None,
    ) -> None:

        if isinstance(value, IProjector):
            self.proj_type = ProjType(type(value).__name__)

            if self.proj_type is not ProjType.NULL:
                self.axis = value._axis

        elif isinstance(value, tuple):
            name, axis = value
            if axis is not None and not len(axis):
                axis = None

            self.proj_type = ProjType(name)
            self.axis = axis

        elif isinstance(value, dict):
            if "name" in value:
                self.proj_type = ProjType(value["name"])
            if "axis" in value:
                self.axis = value["axis"]

        elif value is None:
            self.proj_type = ProjType.NULL
            self.axis = None

        else:
            raise ConfigError(f"Unable to parse {type(value).__name__} as IProjector")

    def check_status(self) -> bool:
        return (self.proj_type is ProjType.NULL) or (
            self.proj_type in (ProjType.AXIAL, ProjType.PLANAR)
            and self.first_axis is not None
        )

    def __set__(
        self, owner, value: tuple[ProjType | str, npt.NDArray[np.floating] | None]
    ):
        self.owner = owner
        self.projector = value

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"proj_type={self.proj_type.name.title()!r}, "
            f"axis={self.axis}"
            ")"
        )
