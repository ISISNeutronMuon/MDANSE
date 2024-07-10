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

import collections

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Signal import differentiate
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms

KB = measure(1.380649e-23, "kg m2/s2 K").toval("uma nm2/ps2 K")


class Temperature(IJob):
    """
    Computes the time-dependent temperature for a given trajectory.
        The temperature is determined from the kinetic energy i.e. the atomic velocities
        which are in turn calculated from the time-dependence of the atomic coordinates.
        Note that if the time step between frames saved in the trajectory is long (~ps)
        compared to the time step in the MD simulations (~fs) the
        velocities are averaged over many configurations and will not give accurate temperatures.
    """

    label = "Temperature"

    category = (
        "Analysis",
        "Thermodynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["interpolation_order"] = (
        "InterpolationOrderConfigurator",
        {
            "label": "velocities",
            "dependencies": {"trajectory": "trajectory"},
            "default": 1,
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        if self.configuration["output_files"]["write_logs"]:
            log_filename = self.configuration["output_files"]["root"] + ".log"
            self.add_log_file_handler(
                log_filename, self.configuration["output_files"]["log_level"]
            )

        self.numberOfSteps = self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_atoms

        self._nFrames = self.configuration["frames"]["number"]

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )
        self._outputData.add(
            "kinetic_energy",
            "LineOutputVariable",
            (self._nFrames,),
            axis="time",
            units="kJ_per_mole",
        )
        self._outputData.add(
            "avg_kinetic_energy",
            "LineOutputVariable",
            (self._nFrames,),
            axis="time",
            units="kJ_per_mole",
        )
        self._outputData.add(
            "temperature",
            "LineOutputVariable",
            (self._nFrames,),
            axis="time",
            units="K",
            main_result=True,
        )
        self._outputData.add(
            "avg_temperature",
            "LineOutputVariable",
            (self._nFrames,),
            axis="time",
            units="K",
        )

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. kineticEnergy (np.array): The calculated kinetic energy
        """

        atom = self._atoms[index]

        symbol = atom.symbol

        mass = ATOMS_DATABASE.get_atom_property(symbol, "atomic_weight")

        trajectory = self.configuration["trajectory"]["instance"]

        if self.configuration["interpolation_order"]["value"] == 0:
            series = trajectory.read_configuration_trajectory(
                index,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
                variable="velocities",
            )
        else:
            series = trajectory.read_atomic_trajectory(
                index,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )

            order = self.configuration["interpolation_order"]["value"]
            for axis in range(3):
                series[:, axis] = differentiate(
                    series[:, axis],
                    order=order,
                    dt=self.configuration["frames"]["time_step"],
                )

        kineticEnergy = 0.5 * mass * np.sum(series**2, 1)

        return index, kineticEnergy

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["kinetic_energy"] += x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nAtoms = len(self._atoms)
        self._outputData["kinetic_energy"] /= nAtoms - 1

        norm = np.arange(1, self._outputData["kinetic_energy"].shape[0] + 1)
        self._outputData["avg_kinetic_energy"][:] = (
            np.cumsum(self._outputData["kinetic_energy"]) / norm
        )

        self._outputData["temperature"][:] = (
            2.0 * self._outputData["kinetic_energy"] / (3.0 * KB)
        )
        self._outputData["avg_temperature"][:] = (
            2.0 * self._outputData["avg_kinetic_energy"] / (3.0 * KB)
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
