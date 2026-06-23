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

from itertools import groupby

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Analysis import mean_square_fluctuation


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
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """Initialize the input parameters and analysis self variables"""
        super().initialize()
        self.numberOfSteps = len(self.trajectory.atom_indices)

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
            (self.numberOfSteps,),
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
        atom_index = self.trajectory.atom_indices[index]
        series = self.trajectory.read_atomic_trajectory(
            atom_index,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )
        rmsf = mean_square_fluctuation(series, root=True)
        return index, rmsf

    def combine(self, index, x):
        """Combines returned results of run_step.

        Parameters
        ----------
        index : int
            The atom index.
        x : float
            The RMSF results for the atom.
        """
        self._outputData["rmsf/all"][index] = x
        name = self._names[index]
        self._outputData[f"rmsf/{name}"][self.ele_idxs[name]] = x
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
