# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/WeightsConfigurator.py
# @brief     Implements module/class/test WeightsConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


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
            raise ConfiguratorError("Invalid type for weight. Must be a string.", self)

        value = value.lower()

        if not value in ATOMS_DATABASE.numeric_properties:
            raise ConfiguratorError(
                "weight %r is not registered as a valid numeric property." % value, self
            )

        self["property"] = value

    def get_weights(self):
        ascfg = self._configurable[self._dependencies["atom_selection"]]

        weights = {}
        for i in range(ascfg["selection_length"]):
            name = ascfg["names"][i]
            for el in ascfg["elements"][i]:
                p = ATOMS_DATABASE[el][self["property"]]
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

        return "selected weight: %s" % self["property"]
