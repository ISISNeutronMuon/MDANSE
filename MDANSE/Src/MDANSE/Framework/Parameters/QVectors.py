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

from typing import TYPE_CHECKING, Any

from MDANSE.Framework.Parameters.Choices import SubclassChoice
from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    Configurable,
    ConfigureDescriptor,
    CustomConfig,
)
from MDANSE.Framework.Parameters.UtilTypes import Depends, DescID, PredictionResult
from MDANSE.Framework.QVectors.IQVectors import IQVectors

if TYPE_CHECKING:
    from collections.abc import Iterator


class QVectors(CustomConfig):
    generator = SubclassChoice[IQVectors, IQVectors](
        IQVectors,
        instance_args={"trajectory": DescID("trajectory")},
        depends={"trajectory": "parent"},
        default="SphericalLatticeQVectors",
    )

    @property
    def params(self) -> dict[DescID, Any]:
        return self.generator.configuration

    @params.setter
    def params(self, value: dict[DescID, Any]):
        self.generator.configuration = value

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory")}

    def __set__(self, owner: Configurable, value):
        self.owner = owner

        match value:
            case (generator, params) | {"generator": generator, **params}:
                self.generator = generator
                self.generator.configuration = params
            case dict():
                self.generator.configuration = value
            case IQVectors():
                self.configuration = value.configuration
            case str():
                self.generator = value
            case _:
                super().__set__(owner, value)

    def validate(self, conf: ConfigureDescriptor, value: Configurable):
        try:
            return self.generator.validate(conf, value)
        except Exception:
            return value

    def preview_output_axis(self, value, raw) -> Iterator[PredictionResult]:
        """Output the values of |Q| from current parameters.

        Yields
        ------
        PredictionResult
            Prediction.
        """
        yield PredictionResult("Q Shells", self.generator.shells, "1/nm")
