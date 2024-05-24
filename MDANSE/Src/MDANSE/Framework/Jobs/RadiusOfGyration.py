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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Analysis import radius_of_gyration


class RadiusOfGyration(IJob):
    """
    The Radius of Gyration can be used, for example, to determine the
    compactness of a molecule. It is calculated as a root (mass weighted)
    mean square distance of the atoms of a molecule relative to its
    centre of mass. ROG can be used to follow the size and spread of
    a molecule during the molecular dynamics simulation.
    """

    label = "Radius of Gyration"

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Computes the pair distribution function for a set of atoms.
        """
        self.numberOfSteps = self.configuration["frames"]["number"]

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        self._outputData.add(
            "rog",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="time",
            units="nm",
            main_result=True,
        )

        self._indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]

        self._masses = np.array(
            [
                m
                for masses in self._configuration["atom_selection"]["masses"]
                for m in masses
            ],
            dtype=np.float64,
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. rog (float): The radius of gyration
        """

        # get the Frame index
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)

        rog = radius_of_gyration(
            conf["coordinates"][self._indexes, :], masses=self._masses, root=True
        )

        return index, rog

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["rog"][index] = x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
