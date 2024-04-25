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

import os

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class MDMCTrajectoryConfigurator(IConfigurator):
    """
    This is a replacement for a trajectory stored in and HDF5 file.
    It is intended to be a drop-in replacement for HDFTrajectoryConfigurator,
    even though it is NOT file-based.
    """

    _default = None

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
        IConfigurator.__init__(self, name, **kwargs)

        self._wildcard = wildcard

    def configure(self, value):
        """
        Configure a HDF trajectory file.

        :param value: an instance of the MdanseTrajectory class
        :type value: MdanseTrajectory from MDMC
        """
        self._original_input = value

        self["value"] = value
        self["filename"] = "MDMC.temp"

        self["instance"] = value

        self["basename"] = "MDMC"

        self["length"] = len(self["instance"])

        self["md_time_step"] = 1.0

        self["has_velocities"] = self["instance"].has_velocity

    def get_information(self):
        """
        Returns some basic informations about the contents of the HDF trajectory file.

        :return: the informations about the contents of the HDF trajectory file.
        :rtype: str
        """

        info = ["MDMC trajectory used as input"]
        info.append("Number of steps: %d\n" % self["length"])
        info.append(
            "Size of the chemical system: %d\n"
            % self["instance"].chemical_system.number_of_atoms
        )
        if self["has_velocities"]:
            info.append("The trajectory contains atomic velocities\n")
        else:
            info.append("The trajectory does not contain atomic velocities\n")

        return "".join(info)
