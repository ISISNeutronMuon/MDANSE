# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/IntegerConfigurator.py
# @brief     Implements module/class/test IntegerConfigurator
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


class IntegerConfigurator(IConfigurator):
    """
    This Configurator allows to input an integer.
    """

    _default = 0

    def __init__(
        self, name, mini=None, maxi=None, choices=None, exclude=None, **kwargs
    ):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param mini: the minimum value allowed for the input value. If None, no restriction for the minimum.
        :type mini: int or None
        :param maxi: the maximum value allowed for the input value. If None, no restriction for the maximum.
        :type maxi: int or None
        :param choices: the list of integers allowed for the input value. If None, any value will be allowed.
        :type choices: int-list or None
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)

        self._mini = int(mini) if mini is not None else None

        self._maxi = int(maxi) if maxi is not None else None

        self._choices = choices if choices is not None else []

        self._exclude = exclude if exclude is not None else ()

    def configure(self, value):
        """
        Configure an integer value.

        :param value: the integer to be configured.
        :type value: int
        """
        self["value"] = self._default

        try:
            value = int(value)
        except (TypeError, ValueError) as e:
            self.error_status = "Wrong input for an integer" + str(e)
            return

        if self._choices:
            if not value in self._choices:
                self.error_status = "the input value is not a valid choice."
                return

        if self._mini is not None:
            if value < self._mini:
                self.error_status = f"the input value is lower than {self._mini}"
                return

        if self._maxi is not None:
            if value > self._maxi:
                self.error_status = f"the input value is higher than {self._maxi}"
                return

        if self._exclude:
            if value in self._exclude:
                self.error_status = f"the input value is forbidden; forbidden values are {self._exclude}"
                return

        self["value"] = value
        self.error_status = "OK"

    @property
    def mini(self):
        """
        Returns the minimum value allowed for an input integer.

        :return: the minimum value allowed for an input value integer.
        :rtype: int or None
        """

        return self._mini

    @property
    def maxi(self):
        """
        Returns the maximum value allowed for an input integer.

        :return: the maximum value allowed for an input value integer.
        :rtype: int or None
        """

        return self._maxi

    @property
    def choices(self):
        """
        Returns the list of integers allowed for an input float.

        :return: the choices allowed for an input float.
        :rtype: int-list or None
        """

        return self._choices

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str
        """

        return "Value: %r" % self["value"]
