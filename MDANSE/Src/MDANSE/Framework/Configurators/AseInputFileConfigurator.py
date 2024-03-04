# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/InputFileConfigurator.py
# @brief     Implements module/class/test InputFileConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from ase.io.formats import all_formats

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator


class AseInputFileConfigurator(InputFileConfigurator):
    """
    This Configurator allows to set an input file.
    """

    _default = ""
    _allowed_formats = ["guess"] + [str(x) for x in all_formats.keys()]

    def __init__(self, name, wildcard="All files|*", **kwargs):
        """
        Initializes the configurator object.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param wildcard: the wildcard used to filter the file. This will be used in MDANSE GUI when
        browsing for the input file.
        :type wildcard: str
        """

        # The base class constructor.
        InputFileConfigurator.__init__(self, name, **kwargs)

        self._wildcard = wildcard
        self["format"] = kwargs.get("format", None)
        self["value"] = ""

    def configure(self, values):
        """
        Configure an input file.

        :param value: the input file.
        :type value: str
        """
        try:
            value, file_format = values
        except ValueError:
            value, file_format = values, None

        value = PLATFORM.get_path(value)

        if not os.path.exists(value):
            print(f"FILE MISSING in {self._name}")
            self.error_status = f"The file {value} does not exist"
            return

        if file_format == "guess":
            file_format = None

        if file_format is not None and not file_format in self._allowed_formats:
            print(f"WRONG FORMAT in {self._name}")
            self.error_status = f"The ASE file format {file_format} is not supported"
            return

        self["value"] = value
        self["filename"] = value
        self["format"] = file_format
        self.error_status = "OK"

    @property
    def wildcard(self):
        """
        Returns the wildcard used to filter the input file.

        :return: the wildcard used to filter the input file.
        :rtype: str
        """

        return self._wildcard

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str
        """
        try:
            val = self["value"]
        except KeyError:
            print(f"No VALUE in {self._name}")

        return "Input file: %r" % self["value"]
