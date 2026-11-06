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
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement_many
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atom_indices_precalculated

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.MemoryConfigurator import MemoryConfigurator


def msd_memory_per_atom(
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
    n_corr_frames = frame_config["n_frames"]
    data_size = 8
    chunk_size = trajectory.chunk_size(array_name="position")
    prefactor = 32 * (n_frames + n_corr_frames) * n_dimensions * data_size / 2**20
    return (prefactor, chunk_size * prefactor, n_atoms * prefactor)


@IJob.register("MeanSquareDisplacement")
class MeanSquareDisplacement(IJob):
    r"""Calculates the mean square displacement (MSD) of atoms in the trajectory.

    The MSD is a representation of diffusion in the system. The motion of an individual
    atom or molecule does not follow a simple path since particles undergo collisions.
    The path is to a good approximation to a random walk.

    Mathematically, a random walk is a series of steps where each step is taken in a
    completely random direction from the one before, as analyzed by Albert Einstein
    in a study of Brownian motion. The MSD of a particle in this case
    is proportional to the time elapsed:

    .. math:: \langle d^{2}(t) \rangle = 6Dt + C

    where :math:`\langle d^{2}(t) \rangle` is the MSD and :math:`t` is the time.
    :math:`D` and :math:`C` are constants. The constant :math:`D` is the so-called
    diffusion coefficient.

    More generally the MSD reveals the distance or volume explored by atoms and
    molecules as a function of time. In crystals, the MSD quickly saturates at a
    constant value which corresponds to the vibrational amplitude.
    Diffusion in a volume will also have a limiting value of the MSD which corresponds
    to the diameter of the volume and the saturation value is reached more slowly.
    The MSD can also reveal e.g. sub-diffusion regimes for the translational
    diffusion of lipids in membranes.
    """

    label = "Mean Square Displacement"

    category = (
        "Analysis",
        "Dynamics",
    )
    PREDICTORS = (
        "frames",
        "memory",
        "running_mode",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["projection"] = (
        "ProjectionConfigurator",
        {},
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
            "mem_function": msd_memory_per_atom,
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
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        n_proc = self.configuration["running_mode"].get("slots", 1)

        self.grouped_indices = group_atom_indices_precalculated(
            self.trajectory,
            self.configuration["frames"]["number"],
            n_proc=n_proc,
            max_group_size=self.configuration["memory"]["atoms_per_step"][0],
        )
        self.numberOfSteps = len(self.grouped_indices)
        self.n_frames = self.configuration["frames"]["n_frames"]

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        # Will store the time.
        self._outputData.add(
            "msd/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        # Will store the mean square displacement evolution.
        for element in self.trajectory.unique_names:
            self._outputData.add(
                f"msd/{element}",
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="msd/axes/time",
                units="nm2",
                main_result=True,
                partial_result=True,
            )
        self._outputData.add(
            "msd/total",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="msd/axes/time",
            units="nm2",
            main_result=True,
        )

        self._atoms = self.trajectory.atom_names

    def run_step(self, index):
        """
        Runs a single step of the job.

        Args:
            index (int): the index of the step

        Returns:
            tuple: the result of the step
        """

        # get selected atom indices sublist
        atom_index_group = self.grouped_indices[index]

        series = self.trajectory.read_atomic_trajectory_many(
            atom_index_group,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        series = self.configuration["projection"]["projector"](series)

        msd = mean_square_displacement_many(
            series, self.configuration["frames"]["n_configs"]
        )

        return index, msd[: self.n_frames]

    def combine(self, step_index, result):
        """
        Combines returned results of run_step.

        Args:
            result (tuple): the output of run_step method
        """
        atom_index_group = self.grouped_indices[step_index]
        # The symbol of the atom.
        for arr_index, at_index in enumerate(atom_index_group):
            element = self._atoms[at_index]

            self._outputData[f"msd/{element}"] += result[:, arr_index]
        self._outputData["msd/total"] += np.sum(result, axis=1)

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        n_atms = self.trajectory.get_total_natoms()

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "msd",
            "LineOutputVariable",
            axis="msd/axes/time",
            units="nm2",
            scaling_factor=False,
            post_func=lambda x: x / n_atms,
            post_label="total",
            main_result=True,
            partial_result=True,
        )

        # The MSDs per element are averaged.
        nAtomsPerElement = self.trajectory.get_natoms()
        for element, number in list(nAtomsPerElement.items()):
            self._outputData[f"msd/{element}"] /= number

        self._outputData["msd/total"] /= n_atms

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
