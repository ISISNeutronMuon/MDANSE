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

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class HDFTrajectoryConfigurator(InputFileConfigurator):
    """
    This configurator allow to input a HDF trajectory file.

    HDF trajectory file is the format used in MDANSE to store Molecular Dynamics trajectories. It is an HDF5 file
    that store various data related to the molecular dynamics : atomic positions, velocities, energies, energy gradients etc...

    To use trajectories derived from MD packages different from HDF, it is compulsory to convert them before to a
    HDF trajectory file.

    :attention: once configured, the HDF trajectory file will be opened for reading.
    """

    _default = "INPUT_FILENAME.mdt"
    _label = "MDANSE trajectory file"

    def configure(self, value):
        """
        Configure a HDF trajectory file.

        :param value: the path for the HDF trajectory file.
        :type value: str
        """
        if value == self._original_input:
            return
        self._original_input = value

        InputFileConfigurator.configure(self, value)
        try:
            trajectory_instance = Trajectory(self["value"])
        except KeyError:
            self.error_status = f"Could not use {value} as input trajectory"
            return

        self["instance"] = trajectory_instance

        self["filename"] = PLATFORM.get_path(trajectory_instance.filename)

        self["basename"] = self["filename"].name

        self["length"] = len(self["instance"])

        time_axis = self["instance"].time()
        try:
            self["md_time_step"] = time_axis[1] - time_axis[0]
        except IndexError:
            self["md_time_step"] = 1.0
        except ValueError:
            self["md_time_step"] = 1.0

        self["has_velocities"] = "velocities" in self["instance"].variables()
