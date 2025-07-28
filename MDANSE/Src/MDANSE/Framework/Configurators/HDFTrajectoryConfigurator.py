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

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class HDFTrajectoryConfigurator(InputFileConfigurator):
    """Chooses the trajectory to be analysed.

    You can use it both with an .mdt file created by an MDANSE converter,
    or with an H5MD file if it contains complete information about the
    atom positions, time axis, physical units and atom types.
    """

    _default = "INPUT_FILENAME.mdt"
    _label = "MDANSE trajectory file"

    def configure_from_instance(self):
        if self._instance is None:
            raise RuntimeError(
                "Running configure_from_instance with no instance defined."
            )
        traj_instance = self._instance
        value = traj_instance._filename

        if value == self._original_input:
            return
        self._original_input = value

        InputFileConfigurator.configure(self, value)

        self.extract_information(traj_instance)

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
        self.extract_information(trajectory_instance)
        self.error_status = "OK"

    def extract_information(self, trajectory_instance: Trajectory):
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

        self.warning_status = trajectory_instance.unit_cell_warning()
