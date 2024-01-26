# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/MultipleChoicesConfigurator.py
# @brief     Implements module/class/test MultipleChoicesConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class MultipleChoicesConfigurator(IConfigurator):
    """
    This Configurator allows to select several items among multiple choices.

    :attention: all the selected items must belong to the allowed selection list.
    """

    _default = []

    def __init__(self, name, choices=None, nChoices=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param choices: the list of values allowed for selection.
        :type choices: list
        :param nChoices: the maximum number of values that can be selected or None if there is no restriction on this number.
        :type nChoices: int or None
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._choices = choices

        self._nChoices = nChoices

    def configure(self, value):
        """
        Configure the input selection list.

        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the input selection list.
        :type value: list
        """

        if self._nChoices is not None:
            if len(value) != self._nChoices:
                raise ConfiguratorError("invalid number of choices.", self)

        indexes = []
        for v in value:
            try:
                indexes.append(self._choices.index(v))
            except ValueError:
                raise ConfiguratorError("%r item is not a valid choice" % v, self)

        if not indexes:
            raise ConfiguratorError("Empty choices selection.", self)

        self["indexes"] = indexes
        self["choices"] = [self._choices[i] for i in indexes]
        self["value"] = self["choices"]

    @property
    def choices(self):
        """
        Returns the list of allowed selection items.

        :return: the list of allowed selection items.
        :rtype: list
        """

        return self._choices

    @property
    def nChoices(self):
        """
        Returns the maximum number items that can be selected or None if there is no restriction on this number.

        :return: the maximum number items that can be selected.
        :rtype: int or None
        """

        return self._nChoices

    def get_information(self):
        return "Selected items: %r" % self["choices"]
