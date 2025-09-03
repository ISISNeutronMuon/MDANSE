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

from collections import defaultdict

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Configurators.SingleChoiceConfigurator import (
    SingleChoiceConfigurator,
)


class WeightsConfigurator(SingleChoiceConfigurator):
    """Select the atom property to be used by the weight scheme.

    This configurator allows to select which atom properties will be used as weights
    when combining the partial contributions into the total result.

    """

    _default = "equal"

    def __init__(self, name: str, **kwargs):
        """Create the configurator.

        Parameters
        ----------
        name : str
            The parent object (IJob) will use this name for this object.

        """
        self._optional_grouping = {}
        self._aliases = {"mass": "atomic_weight"}

        filtered_choices = self.filter_choices()
        SingleChoiceConfigurator.__init__(
            self,
            name,
            choices=filtered_choices,
            **kwargs,
        )

    def filter_choices(self):
        """Limit the list of atom properties to usable values."""
        full_choices = ATOMS_DATABASE.numeric_properties + list(self._aliases.keys())
        to_discard = [x for x in full_choices if "energy" in x]
        to_discard += [
            "abundance",
            "block",
            "color",
            "configuration",
            "element",
            "family",
            "group",
            "state",
        ]
        limited_choices = [x for x in full_choices if x not in to_discard]
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

    def configure(self, value: str):
        """Assign the input value and check validity.

        Parameters
        ----------
        value : str
            Name of an atom property.

        """
        if not self.update_needed(value):
            return

        self._original_input = value
        self._trajectory = self.configurable[self.dependencies["trajectory"]][
            "instance"
        ]

        if not isinstance(value, str):
            self.error_status = "Invalid type for weight. Must be a string."
            return

        value = value.lower()

        if value in self._aliases:
            value = self._aliases[value]

        if value not in self._trajectory.properties:
            self.error_status = (
                f"weight {value} is not registered as a valid numeric property."
            )
            return

        if self.test_values_for_nan(value):
            self.error_status = f"Property {value} is NaN for at leas one atom type."
            return

        self["property"] = value
        self.error_status = "OK"

    def test_values_for_nan(self, property_name: str) -> bool:
        """Throw an error early if weights are not usable."""
        atom_select = self.configurable[self.dependencies["atom_selection"]][
            "flatten_indices"
        ]
        atom_trans = self.configurable[
            self.dependencies["atom_transmutation"]
        ].transmutation
        self._trajectory.set_transmutation(atom_trans)
        self._trajectory.set_selection(atom_select)
        atom_types = np.unique(self._trajectory.atom_types)
        return any(
            np.isnan(self._trajectory.get_atom_property(atom, property_name))
            for atom in atom_types
        )
