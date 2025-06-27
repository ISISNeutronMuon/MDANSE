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

        if value not in self._trajectory.properties_in_database:
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
        atm_select = self.configurable[self.dependencies["atom_selection"]]
        atom_types = np.unique(atm_select["elements"])
        return any(
            np.isnan(self._trajectory.get_atom_property(atom, property_name))
            for atom in atom_types
        )

    def get_weights(
        self, *, prop: str | None = None
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Generate a dictionary of weights.

        Parameters
        ----------
        prop : str or None, optional
            The property to generate the weights from, if None then the
            property set in this configurator will be used.

        Returns
        -------
        tuple[dict[str, float], dict[str, float]]
            The dictionary of the weights.

        """
        if not prop:
            prop = self["property"]

        atm_select = self.configurable[self.dependencies["atom_selection"]]

        weights = []
        for n_elements, atm_names, atm_elements in [
            (atm_select.get_natoms(), atm_select["names"], atm_select["elements"]),
            (
                atm_select.get_all_natoms(),
                atm_select["all_names"],
                atm_select["all_elements"],
            ),
        ]:
            w = defaultdict(float)
            for name, elements in zip(atm_names, atm_elements):
                w[name] += sum(
                    self._trajectory.get_atom_property(element, prop)
                    for element in elements
                )
            for element, num_atoms in n_elements.items():
                w[element] /= num_atoms
            weights.append(w)

        return tuple(weights)
