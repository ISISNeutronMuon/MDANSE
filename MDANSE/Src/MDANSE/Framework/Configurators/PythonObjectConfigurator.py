# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/PythonObjectConfigurator.py
# @brief     Implements module/class/test PythonObjectConfigurator
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


class PythonObjectConfigurator(IConfigurator):
    """
    This Configurator allows to input and evaluate basic python object.

    The python object supported are strings, numbers, tuples, lists, dicts, booleans and None type.

    :note: this configurator is based on a literal and safe evaluation of the input using ast standard library module.
    """

    _default = '""'

    def configure(self, value):
        """
        Configure a python object.

        :param value: the python object to be configured and evaluated.
        :type value: strings, numbers, tuples, lists, dicts, booleans or None type.
        """

        try:
            value = ast.literal_eval(repr(value))
        except SyntaxError as e:
            self.error_status = f"python code SyntaxError: {e}"
            return

        self["value"] = value
        self.error_status = "OK"

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        return "Python object: %r\n" % self["value"]
