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

from typing_extensions import TypeVar, Unpack

from MDANSE.Framework.Parameters.BaseTypes import Integer
from MDANSE.Framework.Parameters.Choices import DynamicSingleChoice
from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    Configurable,
    CustomConfig,
)
from MDANSE.Framework.Parameters.UtilTypes import Depends, DescID

CB = TypeVar("CB", default=str)


class Molecule(DynamicSingleChoice[str, str, CB]):
    default_label = "Molecule name"
    default_tooltip = "Molecule to select."

    def __init__(self, *args, choices: None = None, **kwargs):
        if choices is not None:
            raise ConfigError("Choices cannot be non-None")

        super().__init__(
            *args,
            choices="chemical_system._clusters.keys()",
            **kwargs,
        )


class AtomWithinMolecule(Integer[int | None]):
    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory"), DescID("choices")}

    def get_ranges(self, deps: Depends):
        trajectory = deps["trajectory"]
        molecule = deps["choices"]

        return (0, len(trajectory.chemical_system._clusters[molecule][0]))


class MolecularAxis(CustomConfig):
    molecule = Molecule(depends={"choices": "parent"})
    axis_1 = AtomWithinMolecule(
        default=None,
        depends={"choices": "molecule", "trajectory": "parent"},
        optional=True,
    )
    axis_2 = AtomWithinMolecule(
        default=None,
        depends={"choices": "molecule", "trajectory": "parent"},
        optional=True,
    )

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("choices"), DescID("trajectory")}

    def set_(
        self, molecule: str, axis_1: int | None = None, axis_2: int | None = None
    ) -> None:
        self.molecule = molecule
        self.axis_1 = axis_1
        self.axis_2 = axis_2

    def __set__(
        self,
        owner: Configurable,
        value: tuple[str, Unpack[tuple[int, ...]]] | dict[str, str | int] | str,
    ) -> None:
        self.owner = owner

        match value:
            case [*args]:
                self.set_(*args)
            case dict():
                self.configuration = value
            case str():
                self.molecule = value
            case _:
                super().__set__(owner, value)

    @property
    def details(self) -> str:
        match (self.axis_1, self.axis_2):
            case (None, None):
                return f"Axis in molecule {self.molecule} determined from moment of inertia"
            case (val, None):
                return f"Axis in molecule {self.molecule} from atom {val} to the centre of mass"
            case (val1, val2):
                return f"Axis in molecule {self.molecule} from atom {val1} to {val2}"
