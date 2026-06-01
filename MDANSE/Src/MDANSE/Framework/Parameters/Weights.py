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
from typing_extensions import TypeVar

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Parameters.Choices import SingleChoice
from MDANSE.Framework.Parameters.Parameters import ConfigError
from MDANSE.Framework.Parameters.UtilTypes import Depends, DescID

if TYPE_CHECKING:
    from MDANSE.MolecularDynamics.Trajectory import Trajectory


CB = TypeVar("CB", default=str)


class Weights(SingleChoice[str, str, CB]):
    """Select the atom property to be used by the weight scheme.

    This configurator allows to select which atom properties will be used as weights
    when combining the partial contributions into the total result.

    """

    base_aliases = {"mass": "atomic_weight"}

    def __init__(
        self,
        choices: None = None,
        default: str = "equal",
        aliases: dict[str, str] | None = None,
        **kwargs,
    ):
        """Create the configurator.

        Parameters
        ----------
        name : str
            The parent object (IJob) will use this name for this object.

        """
        self._optional_grouping = {}
        aliases = aliases or {}

        super().__init__(
            default=default,
            aliases=aliases | self.base_aliases,
            choices=None,
            **kwargs,
        )

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {
            DescID("trajectory"),
        }

    def get_choices(self, _deps) -> set[str]:
        """Limit the list of atom properties to usable values."""
        full_choices = set(ATOMS_DATABASE.numeric_properties) | self.aliases.keys()
        limited_choices = full_choices - {
            "abundance",
            "block",
            "color",
            "configuration",
            "element",
            "family",
            "group",
            "state",
        }
        limited_choices -= {x for x in full_choices if "energy" in x}
        self._optional_grouping["xray_group"] = [
            x for x in limited_choices if "xray" in x
        ]
        self._optional_grouping["neutron_group"] = [
            x for x in limited_choices if "b_" in x
        ]
        self._optional_grouping["atomic_group"] = [
            "mass",
            "nucleon",
            "neutron",
            "proton",
        ] + [x for x in limited_choices if "atomic" in x or "radius" in x]
        return limited_choices

    def validate(self, value: str, deps: Depends, /) -> str:
        """Assign the input value and check validity.

        Parameters
        ----------
        value : str
            Name of an atom property.

        """
        value = super().validate(value, deps)

        trajectory: Trajectory = deps["trajectory"]

        if value not in trajectory.properties:
            raise ConfigError(
                f"weight {value} is not registered as a valid numeric property."
            )

        if self.test_values_for_nan(value, deps):
            raise ConfigError(f"Property {value} is NaN for at least one atom type.")

        return value

    def test_values_for_nan(self, property_name: str, deps: Depends, /) -> bool:
        """Throw an error early if weights are not usable."""
        trajectory: Trajectory = deps["trajectory"]

        atom_types = np.unique(trajectory.atom_types)
        return any(
            np.isnan(trajectory.get_atom_property(atom, property_name))
            for atom in atom_types
        )
