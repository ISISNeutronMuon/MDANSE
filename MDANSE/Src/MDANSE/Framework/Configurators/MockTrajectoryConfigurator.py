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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.MockTrajectory import MockTrajectory


class MockTrajectoryConfigurator(IConfigurator):
    """Uses a mock trajectory definition (from JSON) instead of Trajectory.

    This is a replacement for a trajectory stored in and HDF5 file.
    It is intended to be a drop-in replacement for HDFTrajectoryConfigurator,
    even though it is NOT based on an HDF5 file.
    It can use a JSON file with MockTrajectory parameters to create
    a trajectory entirely in the RAM.
    """

    _default = None

    def __init__(self, name, wildcard="JSON file|*.json", **kwargs):
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

    def configure(self, value: str):
        """
        Configure a mock trajectory file.

        :param value: a JSON file with a MockTrajectory definition
        :type value: str
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        self["value"] = value
        self["filename"] = "Mock"

        self["instance"] = MockTrajectory.from_json(value)

        self["basename"] = "Mock"

        self["length"] = len(self["instance"])

        temp = self["instance"].time()
        self["md_time_step"] = temp[1] - temp[0]

        self["has_velocities"] = self["instance"].has_variable("velocities")
