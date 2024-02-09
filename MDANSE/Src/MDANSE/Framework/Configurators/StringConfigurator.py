# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/StringConfigurator.py
# @brief     Implements module/class/test StringConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import ast


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class StringConfigurator(IConfigurator):
    """
    This Configurator allows to input a string.
    """

    _default = ""

    def __init__(self, name, evalType=None, acceptNullString=True, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param evalType: the type to which the string will be evaluated or None if it is let as is.
        :type evalType: python object or None
        :param acceptNullString: if True a null (or blank) string can be input.
        :type acceptNullString: bool
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._evalType = evalType

        self._acceptNullString = acceptNullString

    def configure(self, value):
        """
        Configure an input string.

        :param value: the input string
        :type value: str
        """

        value = str(value)

        if not self._acceptNullString:
            if not value.strip():
                self.error_status = "invalid null string"
                return

        if self._evalType is not None:
            value = ast.literal_eval(value)
            if not isinstance(value, self._evalType):
                self.error_status = (
                    f"the string can not be eval to {self._evalType.__name__} type"
                )
                return

        self["value"] = value
        self.error_status = "OK"

    @property
    def acceptNullString(self):
        """
        Returns whether or not a null (or blank) string is accepted.

        :return: True if a null (or blank) string is accepted as input, False otherwise.
        :rtype: bool
        """

        return self._acceptNullString

    @property
    def evalType(self):
        """
        Returns the type to which the string will be evaluated or None if it is let as is.

        :return: the type to which the string will be evaluated or None if it is let as is.
        :rtype: python object or None
        """

        return self._evalType

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        return "Value: %r" % self["value"]
