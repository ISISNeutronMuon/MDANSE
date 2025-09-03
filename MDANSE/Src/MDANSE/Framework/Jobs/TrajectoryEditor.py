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

import collections
from collections import defaultdict

import numpy as np

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Connectivity import Connectivity
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class TrajectoryEditor(IJob):
    """Write out a modified version of the input trajectory.

    At the moment, the main applications include:

    - molecule detection,
    - setting unit cell parameters,
    - setting partial charges,
    - removing or transmuting atoms,
    - removing frames.
    """

    label = "Trajectory Editor"

    category = ("Trajectory",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, 1, 1)},
    )
    settings["unit_cell"] = (
        "UnitCellConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (np.eye(3), False)},
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
    settings["atom_charges"] = (
        "PartialChargeConfigurator",
        {
            "dependencies": {"trajectory": "trajectory"},
            "default": "{}",
        },
    )
    settings["molecule_tolerance"] = (
        "OptionalFloatConfigurator",
        {
            "default": [False, 0.04],
            "label_text": "Search for molecules (covalent radii plus the tolerance in nm)",
        },
    )
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
        self._input_trajectory = self.trajectory
        self._input_chemical_system = self.configuration["trajectory"][
            "instance"
        ].chemical_system

        if self.configuration["unit_cell"]["apply"]:
            self._new_unit_cell = UnitCell(self.configuration["unit_cell"]["value"])
            self._input_trajectory._trajectory._unit_cells = [
                self._new_unit_cell for _ in range(len(self._input_trajectory))
            ]

        # The collection of atoms corresponding to the atoms selected for output.
        indices = self.trajectory.atom_indices
        self._indices = indices
        temp_copy = list(self._input_chemical_system.atom_list)
        indices_per_element = self.trajectory.get_indices()
        for element, numbers in indices_per_element.items():
            for num in numbers:
                temp_copy[num] = element
        self._selectedAtoms = [temp_copy[ind] for ind in indices]
        name_list = [self._input_chemical_system.name_list[ind] for ind in indices]

        new_chemical_system = ChemicalSystem("Edited system")
        new_chemical_system.initialise_atoms(self._selectedAtoms, name_list)
        if self.configuration["molecule_tolerance"]["use_it"]:
            tolerance = self.configuration["molecule_tolerance"]["value"]
            conn = Connectivity(trajectory=self._input_trajectory, selection=indices)
            conn.find_bonds(tolerance=tolerance)
            conn.add_bond_information(new_chemical_system)
            conf = self.trajectory.configuration(
                self.configuration["frames"]["value"][0]
            )
            coords = conf.coordinates[indices]
            if conf.is_periodic:
                com_conf = PeriodicRealConfiguration(
                    new_chemical_system,
                    coords,
                    conf.unit_cell,
                )
            else:
                com_conf = RealConfiguration(
                    new_chemical_system,
                    coords,
                )
            coords = com_conf.contiguous_configuration().coordinates
        else:
            selected_idxs = set(self._indices)
            indx_map = {j: i for i, j in enumerate(self._indices)}

            selected_bonds = [
                (indx_map[i], indx_map[j])
                for i, j in self._input_chemical_system._bonds
                if i in selected_idxs and j in selected_idxs
            ]
            new_chemical_system.add_bonds(selected_bonds)

            selected_clusters = defaultdict(list)
            for key, vals in self._input_chemical_system._clusters.items():
                for val in vals:
                    new_cluster = set(val) & selected_idxs
                    if new_cluster:
                        new_cluster = sorted([indx_map[i] for i in new_cluster])
                        selected_clusters[key].append(new_cluster)

            new_chemical_system._clusters = selected_clusters

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            new_chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
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

        conf = self.trajectory.configuration(frameIndex)
        conf = conf.contiguous_configuration(bring_to_centre=True)
        charges = self.trajectory.charges(frameIndex)
        coords = conf.coordinates

        variables = {}
        if self.trajectory.has_variable("velocities"):
            variables["velocities"] = self.trajectory.variable("velocities")[
                frameIndex, self._indices, :
            ].astype(np.float64)
        if self.trajectory.has_variable("gradients"):
            variables["gradients"] = self.trajectory.variable("gradients")[
                frameIndex, self._indices, :
            ].astype(np.float64)

        if conf.is_periodic:
            com_conf = PeriodicRealConfiguration(
                self._output_trajectory.chemical_system,
                coords[self._indices],
                conf.unit_cell,
                **variables,
            )
        else:
            com_conf = RealConfiguration(
                self._output_trajectory.chemical_system,
                coords[self._indices],
                **variables,
            )

        new_charges = np.zeros(len(self._indices))
        for number, at_index in enumerate(self._indices):
            try:
                q = self.configuration["atom_charges"]["charges"][at_index]
            except KeyError:
                q = charges[at_index]
            new_charges[number] = q

        # The times corresponding to the running index.
        time = self.configuration["frames"]["time"][index]

        self._output_trajectory.dump_configuration(com_conf, time)
        self._output_trajectory.write_charges(new_charges, index)

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
        self.trajectory.close()

        # The output trajectory is closed.
        self._output_trajectory.write_standard_atom_database()
        write_metadata(self, self._output_trajectory._h5_file)
        self._output_trajectory.close()
        super().finalize()
