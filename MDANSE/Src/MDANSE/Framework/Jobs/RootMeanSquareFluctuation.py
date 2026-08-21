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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Analysis import mean_square_fluctuation
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atom_indices_precalculated

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.MemoryConfigurator import MemoryConfigurator


def rmsf_memory_per_atom(
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


@IJob.register("RootMeanSquareFluctuation")
class RootMeanSquareFluctuation(IJob):
    """Calculates the Root Mean Square Fluctuation of atom positions.

    The root mean square fluctuation (RMSF) for a set of atoms is similar to the
    square root of the mean square displacement (MSD), except that it is spatially
    resolved rather than time resolved. It reveals the dynamical heterogeneity
    of the molecule over the course of an MD simulation.

    As opposed to most analysis types, the result is a single number per atom index.
    """

    label = "Root Mean Square Fluctuation"

    category = (
        "Analysis",
        "Dynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "choices": ["atom", "molecule"],
            "default": "atom",
            "dependencies": {
                "trajectory": "trajectory",
            },
        },
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["memory"] = (
        "MemoryConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "frames": "frames",
            },
            "mem_function": rmsf_memory_per_atom,
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
        """Initialize the input parameters and analysis self variables"""
        super().initialize()

        n_proc = self.configuration["running_mode"].get("slots", 1)

        self.grouped_indices = group_atom_indices_precalculated(
            self.trajectory,
            self.configuration["frames"]["number"],
            n_proc=n_proc,
            max_group_size=self.configuration["memory"]["atoms_per_step"][0],
        )
        self.numberOfSteps = len(self.grouped_indices)

        self.group_molecules = self.configuration["grouping_level"]["value"] != "atom"
        self.ele_idxs = {}

        all_names = self.trajectory.atom_names
        self._names = [all_names[index] for index in self.trajectory.atom_indices]

        self._outputData.add(
            "rmsf/axes/indices/all",
            "LineOutputVariable",
            self.trajectory.atom_indices,
        )
        self._outputData.add(
            "rmsf/all",
            "LineOutputVariable",
            (len(self.trajectory.atom_indices),),
            axis="rmsf/axes/indices/all",
            units="nm",
            main_result=True,
        )

        if self.group_molecules:
            self.group_indices = {
                grp: {
                    job_i: at_i
                    for job_i, at_i in enumerate(self.trajectory.atom_indices)
                    if f"<{grp}>" in self._names[job_i]
                }
                for grp in self.trajectory.group_lookup
            }
        else:
            self.group_indices = {}

        for name in self.trajectory.unique_names:
            idxs = [
                at_i
                for job_i, at_i in enumerate(self.trajectory.atom_indices)
                if self._names[job_i] == name
            ]
            self.ele_idxs[name] = 0
            self._outputData.add(
                f"rmsf/axes/indices/{name}",
                "LineOutputVariable",
                idxs,
            )
            self._outputData.add(
                f"rmsf/{name}",
                "LineOutputVariable",
                (len(idxs),),
                axis=f"rmsf/axes/indices/{name}",
                units="nm",
            )

        for grp, index_dict in self.group_indices.items():
            self._outputData.add(
                f"rmsf/axes/indices/<{grp}>/all",
                "LineOutputVariable",
                index_dict.values(),
            )
            self._outputData.add(
                f"rmsf/<{grp}>/all",
                "LineOutputVariable",
                (len(index_dict),),
                axis=f"rmsf/axes/indices/<{grp}>/all",
                units="nm",
            )

    def run_step(self, index):
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            The atom index.

        Returns
        -------
        set[int, float]
            The atom index and the calculated root mean square
            fluctuation for that atom.
        """
        atom_index_group = self.grouped_indices[index]

        series = self.trajectory.read_atomic_trajectory_many(
            atom_index_group,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )
        rmsf = mean_square_fluctuation(series, root=True, sum_axis=2)
        return index, rmsf

    def combine(self, step_index, x):
        """Combines returned results of run_step.

        Parameters
        ----------
        index : int
            The atom index.
        x : float
            The RMSF results for the atom.
        """
        atom_index_group = self.grouped_indices[step_index]
        # The symbol of the atom.
        for arr_index, at_index in enumerate(atom_index_group):
            self._outputData["rmsf/all"][at_index] = x[arr_index]
            name = self._names[at_index]
            self._outputData[f"rmsf/{name}"][self.ele_idxs[name]] = x[arr_index]
            self.ele_idxs[name] += 1

    def finalize(self):
        """Finalizes the calculations (e.g. averaging the total term, output
        files creations ...).
        """
        if self.group_molecules:
            for grp, index_dict in self.group_indices.items():
                for result_in, job_in in enumerate(index_dict.keys()):
                    self._outputData[f"rmsf/<{grp}>/all"][result_in] = self._outputData[
                        "rmsf/all"
                    ][job_in]

        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
