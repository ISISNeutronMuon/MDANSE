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

from typing import TYPE_CHECKING

import numpy as np

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atom_indices_precalculated

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.MemoryConfigurator import MemoryConfigurator


def rmsd_memory_per_atom(
    mem_conf: MemoryConfigurator, n_atoms: int = 1
) -> tuple[int, int, int]:
    """Calculate the memory requirements of a DISF calculation.

    The data size is fixed as 8 bytes per number, since the arrays allocated
    by numpy in this analysis are most likely going to be float64, even
    if the coordinates in the input trajectory are float32.

    Parameters
    ----------
    mem_conf : MemoryConfigurator
        The configurator instance which contains the needed inputs
    n_atoms : int, optional
        Use a specific number of atoms in the calculation, by default 1

    Returns
    -------
    tuple[int, int int]
        MB per atom, per chunk and per n_atoms from input, respectively
    """
    trajectory = mem_conf.configurable[mem_conf.dependencies["trajectory"]]["instance"]
    frame_config = mem_conf.configurable[mem_conf.dependencies["frames"]]
    n_dimensions = 3
    n_frames = frame_config["number"]
    data_size = 8
    chunk_size = trajectory.chunk_size(array_name="position")
    prefactor = 4 * n_frames * n_dimensions * data_size / 2**20
    return (prefactor, chunk_size * prefactor, n_atoms * prefactor)


@IJob.register("RootMeanSquareDeviation")
class RootMeanSquareDeviation(IJob):
    """Calculates the Root Mean Square Deviation of the selected atoms.

    The Root Mean-Square Deviation (RMSD) is one of the most popular measures
    of structural similarity. It is a numerical measure of the difference
    between two structures. Typically, the RMSD is used to quantify the structural
    evolution of the system during the simulation. It can provide essential
    information about the structure, if it reached equilibrium or conversely
    if major structural changes occurred during the simulation.
    """

    label = "Root Mean Square Deviation"

    category = (
        "Analysis",
        "Dynamics",
    )
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["reference_frame"] = (
        "IntegerConfigurator",
        {"mini": 0, "default": 0, "label": "Trajectory frame used as reference"},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
        },
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_transmutation"] = (
        "AtomTransmutationConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
        },
    )
    settings["memory"] = (
        "MemoryConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "frames": "frames",
            },
            "mem_function": rmsd_memory_per_atom,
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = (
        "RunningModeConfigurator",
        {
            "dependencies": {
                "memory": "memory",
            }
        },
    )

    def initialize(self):
        super().initialize()

        n_proc = self.configuration["running_mode"].get("slots", 1)

        self.grouped_indices = group_atom_indices_precalculated(
            self.trajectory,
            self.configuration["frames"]["number"],
            n_proc=n_proc,
            max_group_size=self.configuration["memory"]["atoms_per_step"][0],
        )
        self.numberOfSteps = len(self.grouped_indices)

        self._referenceIndex = self.configuration["reference_frame"]["value"]

        # Will store the time.
        self._outputData.add(
            "rmsd/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        # Will initially store the mean square deviation before appling the root
        for element in self.trajectory.unique_names:
            self._outputData.add(
                f"rmsd/{element}",
                "LineOutputVariable",
                (self.configuration["frames"]["number"],),
                axis="rmsd/axes/time",
                units="nm",
                main_result=True,
                partial_result=True,
            )
        self._outputData.add(
            "rmsd/total",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="rmsd/axes/time",
            units="nm",
            main_result=True,
        )

        self._atoms = self.trajectory.atom_names

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        atom_index_group = self.grouped_indices[index]

        series = self.trajectory.read_atomic_trajectory_many(
            atom_index_group,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        # Compute the squared sum of the difference between all the coordinate of atoms i and the reference ones
        squaredDiff = np.sum((series - series[self._referenceIndex, :, :]) ** 2, axis=2)

        return index, squaredDiff

    def combine(self, step_index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        atom_index_group = self.grouped_indices[step_index]
        for arr_index, at_index in enumerate(atom_index_group):
            element = self._atoms[at_index]

            self._outputData[f"rmsd/{element}"] += x[:, arr_index]
        self._outputData["rmsd/total"] += np.sum(x, axis=1)

    def finalize(self):
        """
        Finalize the job.
        """
        n_atms = self.trajectory.get_total_natoms()

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "rmsd",
            "LineOutputVariable",
            axis="rmsd/axes/time",
            units="nm",
            scaling_factor=False,
            post_func=lambda x: np.sqrt(x / n_atms),
            post_label="total",
            main_result=True,
            partial_result=True,
        )

        nAtomsPerElement = self.trajectory.get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"rmsd/{element}"][:] = np.sqrt(
                self._outputData[f"rmsd/{element}"] / number
            )

        self._outputData["rmsd/total"][:] = np.sqrt(
            self._outputData["rmsd/total"] / n_atms
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
