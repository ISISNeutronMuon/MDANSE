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

from MDANSE.Framework.Configurators.MDTrajAnalysisConfigurator import MDTRAJ_JOBS
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.mdtraj.trajectory import build_mdtraj_trajectory


@IJob.register("MDTrajAnalysis")
class MDTrajAnalysis(IJob):
    """This wrapper allows you to run different analysis types
    implemented in MDTraj, but using an MDANSE trajectory as input.
    """

    label = "MDTraj Analysis"

    category = (
        "Analysis",
        "External",
    )
    PREDICTORS = ()

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
    settings["mdtraj_analysis"] = (
        "MDTrajAnalysisConfigurator",
        {},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = 1

        self.frame_slice = (
            self.configuration["frames"]["first"],
            self.configuration["frames"]["last"],
            self.configuration["frames"]["step"],
        )
        self.analysis_function = self.configuration["mdtraj_analysis"]["function"]
        self.analysis_args = self.configuration["mdtraj_analysis"]["args"]
        self.analysis_kwargs = self.configuration["mdtraj_analysis"]["kwargs"]

    def run_step(self, index):
        mdtraj_trajectory = build_mdtraj_trajectory(
            self.trajectory, frame_slice=self.frame_slice
        )
        function = MDTRAJ_JOBS[self.analysis_function]
        result = function(
            mdtraj_trajectory, *self.analysis_args, **self.analysis_kwargs
        )
        return index, result

    def combine(self, _, result):
        self.result = result

    def finalize(self):
        print(self.result)
