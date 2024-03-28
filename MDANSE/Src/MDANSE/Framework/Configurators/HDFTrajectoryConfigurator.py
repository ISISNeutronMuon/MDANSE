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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now

import os

from MDANSE import PLATFORM

from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator
from MDANSE.Framework.InputData.IInputData import IInputData


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

        InputFileConfigurator.configure(self, value)

        inputTraj = IInputData.create("HDFTrajectoryInputData", self["value"])

        self["hdf_trajectory"] = inputTraj

        self["instance"] = inputTraj.trajectory

        self["filename"] = PLATFORM.get_path(inputTraj.filename)

        self["basename"] = os.path.basename(self["filename"])

        self["length"] = len(self["instance"])

        try:
            self["md_time_step"] = (
                self["instance"].file["/time"][1] - self["instance"].file["/time"][0]
            )
        except IndexError:
            self["md_time_step"] = 1.0

        self["has_velocities"] = "velocities" in self["instance"].file["/configuration"]

    def get_information(self):
        """
        Returns some basic informations about the contents of the HDF trajectory file.

        :return: the informations about the contents of the HDF trajectory file.
        :rtype: str
        """

        info = ["HDF input trajectory: %r\n" % self["filename"]]
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
