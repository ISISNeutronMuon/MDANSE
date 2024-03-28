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


from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.SingleChoiceConfigurator import (
    SingleChoiceConfigurator,
)


class WeightsConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to select how the properties that depends on atom type will be weighted when computing
    the total contribution of all atoms.

    Any numeric property defined in MDANSE.Data.ElementsDatabase.ElementsDatabase can be used as a weigh.
    """

    _default = "equal"

    def __init__(self, name, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        """

        SingleChoiceConfigurator.__init__(
            self, name, choices=ATOMS_DATABASE.numeric_properties, **kwargs
        )

    def configure(self, value):
        """
        Configure the weight.

        :param value: the name of the weight to use.
        :type value: one of the numeric properties of MDANSE.Data.ElementsDatabase.ElementsDatabase
        """

        if not isinstance(value, str):
            self.error_status = "Invalid type for weight. Must be a string."
            return

        value = value.lower()

        if not value in ATOMS_DATABASE.numeric_properties:
            self.error_status = (
                f"weight {value} is not registered as a valid numeric property."
            )
            return

        self["property"] = value
        self.error_status = "OK"

    def get_weights(self):
        ascfg = self._configurable[self._dependencies["atom_selection"]]

        weights = {}
        for i in range(ascfg["selection_length"]):
            name = ascfg["names"][i]
            for el in ascfg["elements"][i]:
                p = ATOMS_DATABASE.get_atom_property(el, self["property"])
                if name in weights:
                    weights[name] += p
                else:
                    weights[name] = p

        for k, v in list(ascfg.get_natoms().items()):
            weights[k] /= v

        return weights

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        return "selected weight: %s\n" % self["property"]
