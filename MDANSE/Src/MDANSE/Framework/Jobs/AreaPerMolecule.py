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
import os

import numpy as np


from MDANSE.Core.Error import Error
from MDANSE.Framework.Jobs.IJob import IJob


class AreaPerMoleculeError(Error):
    pass


class AreaPerMolecule(IJob):
    """
    Computes the area per molecule.

    The area per molecule is computed by simply dividing the surface of one of the simulation box faces
    (*ab*, *bc* or *ac*) by the number of molecules with a given name. This property should be a constant unless
    the simulation performed was in the NPT ensemble. This analysis is relevant for oriented structures like lipid membranes.
    """

    label = "Area Per Molecule"

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
    settings["axis"] = (
        "SingleChoiceConfigurator",
        {
            "label": "area vectors",
            "choices": ["ab", "bc", "ac"],
            "default": "ab",
        },
    )
    settings["molecule_name"] = (
        "MoleculeSelectionConfigurator",
        {
            "label": "molecule name",
            "default": "",
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the analysis (open trajectory, create output variables ...)
        """

        # This will define the number of steps of the analysis. MUST be defined for all analysis.
        self.numberOfSteps = self.configuration["frames"]["number"]

        # Extract the indexes corresponding to the axis selection (a=0,b=1,c=2).
        axis_labels = self.configuration["axis"]["value"]
        if axis_labels == "ab":
            self._axisIndexes = [0, 1]
        elif axis_labels == "bc":
            self._axisIndexes = [1, 2]
        else:
            self._axisIndexes = [0, 2]

        # The number of molecules that match the input name. Must be > 0.
        self._nMolecules = len(
            [
                ce
                for ce in self.configuration["trajectory"][
                    "instance"
                ].chemical_system.chemical_entities
                if ce.name == self.configuration["molecule_name"]["value"]
            ]
        )
        if self._nMolecules == 0:
            raise AreaPerMoleculeError(
                "No molecule matches %r name."
                % self.configuration["molecule_name"]["value"]
            )

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        self._outputData.add(
            "area_per_molecule",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="time",
            units="1/nm2",
            main_result=True,
        )

    def run_step(self, index):
        """
        Run a single step of the analysis

        :Parameters:
            #. index (int): the index of the step.
        :Returns:
            #. index (int): the index of the step.
            #. area per molecule (float): the calculated area per molecule for this step
        """

        # Get the frame index
        frame_index = self.configuration["frames"]["value"][index]

        configuration = self.configuration["trajectory"]["instance"].configuration(
            frame_index
        )

        try:
            unit_cell = configuration.unit_cell._unit_cell
            normalVect = np.cross(
                unit_cell[self._axisIndexes[0]], unit_cell[self._axisIndexes[1]]
            )
        except:
            raise AreaPerMoleculeError(
                "The unit cell must be defined for AreaPerMolecule"
            )

        apm = np.sqrt(np.sum(normalVect**2)) / self._nMolecules

        return index, apm

    def combine(self, index, x):
        """
        Update the output each time a step is performed
        """

        self._outputData["area_per_molecule"][index] = x

    def finalize(self):
        """
        Finalize the analysis (close trajectory, write output data ...)
        """

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )
        self.configuration["trajectory"]["instance"].close()
