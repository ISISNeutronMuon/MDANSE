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

import numpy as np

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Signal import differentiate_many
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atom_indices

KB = measure(1.380649e-23, "kg m2/s2 K").toval("Da nm2/ps2 K")


@IJob.register("Temperature")
class Temperature(IJob):
    """Calculates the temperature of the system for every selected frame.

    Computes the time-dependent temperature for a given trajectory.
    The temperature is determined from the kinetic energy i.e. the atomic velocities
    which are in turn calculated from the time-dependence of the atomic coordinates.

    Note that the velocity calculated from atom positions will be underestimated
    and the error in the results will be larger for trajectories with
    a large step between (saved) frames compared to the actual time step of the
    MD simulations (~fs).
    """

    label = "Temperature"

    category = (
        "Analysis",
        "Thermodynamics",
    )
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["interpolation_order"] = (
        "InterpolationOrderConfigurator",
        {
            "dependencies": {"trajectory": "trajectory", "frames": "frames"},
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.trajectory.set_selection(
            [
                index
                for index, symbol in enumerate(self.trajectory.atom_types)
                if symbol in self.trajectory.non_dummy_elements
            ]
        )
        n_proc = self.configuration["running_mode"].get("slots", 1)

        self.grouped_indices = group_atom_indices(
            self.trajectory, n_proc=n_proc, memory_scale_factor=2
        )
        self.numberOfSteps = len(self.grouped_indices)

        self._nFrames = self.configuration["frames"]["number"]

        self._outputData.add(
            "temp/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )
        self._outputData.add(
            "temp/kinetic_energy",
            "LineOutputVariable",
            (self._nFrames,),
            axis="temp/axes/time",
            units="kJ_per_mole",
        )
        self._outputData.add(
            "temp/avg_kinetic_energy",
            "LineOutputVariable",
            (self._nFrames,),
            axis="temp/axes/time",
            units="kJ_per_mole",
        )
        self._outputData.add(
            "temp/temperature",
            "LineOutputVariable",
            (self._nFrames,),
            axis="temp/axes/time",
            units="K",
            main_result=True,
        )
        self._outputData.add(
            "temp/avg_temperature",
            "LineOutputVariable",
            (self._nFrames,),
            axis="temp/axes/time",
            units="K",
        )

        self._atoms = self.trajectory.atom_names

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. kineticEnergy (np.array): The calculated kinetic energy
        """
        atom_index_group = self.grouped_indices[index]

        mass = np.array(
            [
                self.trajectory.get_atom_property(
                    self._atoms[at_index], "atomic_weight"
                )
                for at_index in atom_index_group
            ]
        )

        trajectory = self.trajectory

        if self.configuration["interpolation_order"]["value"] == 0:
            series = trajectory.read_configuration_trajectory(
                atom_index_group,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
                variable="velocities",
            )
        else:
            series = trajectory.read_atomic_trajectory_many(
                atom_index_group,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )

            order = self.configuration["interpolation_order"]["value"]
            series = differentiate_many(
                series,
                order=order,
                dt=self.configuration["frames"]["time_step"],
            )

        kineticEnergy = 0.5 * mass[None, :] * np.sum(series**2, axis=2)

        return index, kineticEnergy

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["temp/kinetic_energy"] += np.sum(x, axis=1)

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nAtoms = len(self.trajectory.atom_indices)
        self._outputData["temp/kinetic_energy"] /= nAtoms - 1

        norm = np.arange(1, self._outputData["temp/kinetic_energy"].shape[0] + 1)
        self._outputData["temp/avg_kinetic_energy"][:] = (
            np.cumsum(self._outputData["temp/kinetic_energy"]) / norm
        )

        self._outputData["temp/temperature"][:] = (
            2.0 * self._outputData["temp/kinetic_energy"] / (3.0 * KB)
        )
        self._outputData["temp/avg_temperature"][:] = (
            2.0 * self._outputData["temp/avg_kinetic_energy"] / (3.0 * KB)
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
