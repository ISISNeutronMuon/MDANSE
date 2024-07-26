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
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)


class TrajectoryEditor(IJob):
    """
    This job will gradually gain more features. The main intent
    is to allow the users to modify an existing trajectory, in case
    some of the information was missing or needed correcting.
    """

    label = "Trajectory Editor"

    category = (
        "Analysis",
        "Trajectory",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, -1, 1)},
    )
    settings["unit_cell"] = (
        "UnitCellConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": np.eye(3)},
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
                "atom_selection": "atom_selection",
            }
        },
    )
    # settings["atom_charges"] = (
    #     "PartialChargeConfigurator",
    #     {
    #         "dependencies": {"trajectory": "trajectory"},
    #         "default": {},
    #     },
    # )
    # settings["molecule_tolerance"] = (
    #     "FloatConfigurator",
    #     {"default": 0.25},
    # )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {"format": "MDTFormat"},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]
        self._input_trajectory = self.configuration["trajectory"]["instance"]

        self._new_unit_cell = UnitCell(self.configuration["unit_cell"]["value"])
        self._input_trajectory._trajectory._unit_cells = [
            self._new_unit_cell for _ in range(len(self._input_trajectory))
        ]

        atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

        # The collection of atoms corresponding to the atoms selected for output.
        indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]
        self._indices = indexes
        self._selectedAtoms = [atoms[ind] for ind in indexes]
        elements = self.configuration["atom_selection"]["elements"]

        new_chemical_system = ChemicalSystem("Edited system")
        new_chemical_system.from_element_list([entry[0] for entry in elements])

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            new_chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            compression=self.configuration["output_files"]["compression"],
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. None
        """

        # get the Frame index
        frameIndex = self.configuration["frames"]["value"][index]

        n_coms = self._output_trajectory.chemical_system.number_of_atoms

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)
        conf = conf.contiguous_configuration()

        coords = conf.coordinates

        variables = {}
        if self.configuration["trajectory"]["instance"].has_variable("velocities"):
            variables = {
                "velocities": self.configuration["trajectory"]["instance"]
                .variable("velocities")[frameIndex, :, :]
                .astype(np.float64)
            }

        if conf.is_periodic:
            com_conf = PeriodicRealConfiguration(
                self._output_trajectory.chemical_system,
                coords[self._indices],
                conf.unit_cell,
                **variables,
            )
        else:
            com_conf = RealConfiguration(
                self._output_trajectory.chemical_system, coords, **variables
            )

        self._output_trajectory.chemical_system.configuration = com_conf

        # The times corresponding to the running index.
        time = self.configuration["frames"]["time"][index]

        self._output_trajectory.dump_configuration(time)

        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # The input trajectory is closed.
        self.configuration["trajectory"]["instance"].close()

        # The output trajectory is closed.
        self._output_trajectory.close()
        super().finalize()
