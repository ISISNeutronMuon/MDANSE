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
import json

import numpy as np
from copy import deepcopy

import h5py

from MDANSE.Chemistry.ChemicalEntity import AtomGroup
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Signal import filter_map
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms, TrajectoryWriter
from MDANSE.MLogging import LOG


class TrajectoryFilter(IJob):
    """
    Design and apply a filter for the atomic trajectories.
    """

    label = "Trajectory Filter"

    category = (
        "Analysis",
        "Dynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {"dependencies": {"trajectory": "trajectory", "frames": "frames"}},
    )
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
    )
    settings["trajectory_filter"] = (
        "TrajectoryFilterConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
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
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "atomic_weight",
            "dependencies": {"atom_selection": "atom_selection"},
        },
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {"format": "MDTFormat"},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )
        self._selected_atoms = []
        for indexes in self.configuration["atom_selection"]["indexes"]:
            for idx in indexes:
                self._selected_atoms.append(self._atoms[idx])
        self._selected_atoms = AtomGroup(self._selected_atoms)

        self._trajectories = np.zeros_like(
            np.zeros(3*len(self._atoms)*len(self.configuration["frames"]["value"])).reshape((
                len(self._atoms),
                3,
                len(self.configuration["frames"]["value"])
            ))
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        """
        LOG.debug(f"Running step: {index}")
        trajectory = self.configuration["trajectory"]["instance"]

        # get atom index
        indexes = self.configuration["atom_selection"]["indexes"][index]
        atoms = [self._atoms[idx] for idx in indexes]

        series = trajectory.read_com_trajectory(
            atoms,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        self._trajectories[index] = series.T
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

        # Get filter class and instantiate filter object
        filter_config = json.loads(self.configuration["trajectory_filter"]['value'])
        filter_class, filter_attributes = filter_map[filter_config["filter"]], filter_config["attributes"]

        filter = filter_class(**filter_attributes)

        # Get trajectories from current instance chemical system
        filtered_chemical_system = deepcopy(self.configuration["trajectory"]["instance"].chemical_system)

        # Apply filter
        filtered_coords = apply(filter, self._trajectories)

        ### filtered_chemical_system._configuration.variables["coordinates"] = coords

        # Create trajectory writer object
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            filtered_chemical_system,
            self.numberOfSteps,
            self._selected_atoms.atom_list,
            positions_dtype=self.configuration["output_files"]["dtype"],
            compression=self.configuration["output_files"]["compression"],
        )

        for t in range(filter_attributes["n_steps"]):
            self._output_trajectory.dump_configuration(t, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"})

        # The input trajectory is closed.
        self.configuration["trajectory"]["instance"].close()

        # The output trajectory is closed.
        self._output_trajectory.close()

        outputFile = h5py.File(self.configuration["output_files"]["file"], "r+")

        # Write filter attributes to output data
        #outputFile.create_dataset("rms", data=self._rms, dtype=np.float64)

        outputFile.close()
        super().finalize()

def apply(filter, trajectories):
    """

    """
    for atom in trajectories:
        x, y, z = atom
        for component in zip(x, y, z):
            component = filter.apply(component)
    return trajectories

