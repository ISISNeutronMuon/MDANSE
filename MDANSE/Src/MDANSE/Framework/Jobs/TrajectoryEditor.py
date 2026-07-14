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

import more_itertools
import numpy as np

from MDANSE.Chemistry.ChemicalSystem import (
    ChemicalSystem,
    assign_molecules_after_atom_selection,
)
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Connectivity import Connectivity
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


@IJob.register("TrajectoryEditor")
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

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, 1, 1)},
    )
    settings["unit_cell"] = (
        "UnitCellConfigurator",
        {
            "dependencies": {"trajectory": "trajectory"},
            "default": ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], False),
        },
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {
            "dependencies": {"trajectory": "trajectory"},
            "default": """\
{
   "0": {"function_name": "select_all", "operation_type": "union"}
}""",
        },
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
            "label": "Detect molecules",
            "tooltip": "Accept bonds for distances lower than sum of the covalent radii and this tolerance margin",
            "label_text": "Search for molecules (covalent radii plus the tolerance in nm)",
        },
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "format": "MDTFormat",
        },
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.number_of_frames = self.configuration["frames"]["number"]
        self._input_trajectory = self.trajectory
        self._input_chemical_system = self.configuration["trajectory"][
            "instance"
        ].chemical_system

        chunk_size = self.configuration["output_files"]["chunk_size"]
        atoms_per_chunk = chunk_size[1] if isinstance(chunk_size, tuple) else chunk_size
        frames_per_chunk = chunk_size[0] if isinstance(chunk_size, tuple) else 1

        n_time_steps = np.ceil(self.number_of_frames / frames_per_chunk).astype(int)

        self.grouped_indices = list(
            more_itertools.chunked(self.trajectory.atom_indices, atoms_per_chunk)
        )
        self.numberOfSteps = len(self.grouped_indices) * n_time_steps
        self.n_atom_chunks = len(self.grouped_indices)
        self.n_frame_chunks = n_time_steps
        self.atoms_per_chunk = atoms_per_chunk
        self.frames_per_chunk = frames_per_chunk
        self.grouped_frames = list(
            more_itertools.chunked(
                range(
                    self.configuration["frames"]["first"],
                    self.configuration["frames"]["last"] + 1,
                    self.configuration["frames"]["step"],
                ),
                frames_per_chunk,
            )
        )

        if self.configuration["unit_cell"]["apply"]:
            self._new_unit_cell = UnitCell(
                np.array(self.configuration["unit_cell"]["value"])
            )
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
            conn = Connectivity(
                trajectory=self._input_trajectory, selection=indices, parallel_workers=1
            )
            conn.find_bonds(tolerance=tolerance)
            conn.add_bond_information(new_chemical_system)
            self.cluster_indices = list(
                more_itertools.flatten(new_chemical_system.clusters.values())
            )
        else:
            assign_molecules_after_atom_selection(
                self._indices, self._input_chemical_system, new_chemical_system
            )
            self.cluster_indices = list(
                more_itertools.flatten(new_chemical_system.clusters.values())
            )

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            new_chemical_system,
            self.number_of_frames,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
            meta_block_size=self.configuration["output_files"]["meta_block_size"],
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

        chunk_index = index % self.n_atom_chunks
        frame_index = index // self.n_atom_chunks

        atom_index_group = self.grouped_indices[chunk_index]
        frame_index_group = self.grouped_frames[frame_index]

        if len(frame_index_group) == 1:
            frame_index_slice = slice(frame_index_group[0], frame_index_group[0] + 1)
        else:
            frame_index_slice = slice(
                frame_index_group[0],
                frame_index_group[-1] + 1,
                frame_index_group[1] - frame_index_group[0],
            )

        target_atoms = slice(
            chunk_index * self.atoms_per_chunk, (chunk_index + 1) * self.atoms_per_chunk
        )
        target_frames = slice(
            frame_index * self.frames_per_chunk,
            (frame_index + 1) * self.frames_per_chunk,
        )
        target_frame_list = list(
            range(
                frame_index * self.frames_per_chunk,
                min((frame_index + 1) * self.frames_per_chunk, self.number_of_frames),
            )
        )

        series = self.trajectory.coordinates(frame_index_slice, atom_index_group)
        self._output_trajectory.write_array_fragment(
            series,
            "coordinates",
            atom_indices=target_atoms,
            frame_indices=target_frames,
        )
        if self.trajectory.has_variable("velocities"):
            velocity_series = self.trajectory.read_configuration_trajectory(
                atom_index_group,
                slc=frame_index_slice,
                variable="velocities",
            )
            self._output_trajectory.write_array_fragment(
                velocity_series,
                "velocities",
                atom_indices=target_atoms,
                frame_indices=target_frames,
            )
        if self.trajectory.has_variable("gradients"):
            gradient_series = self.trajectory.read_configuration_trajectory(
                atom_index_group,
                slc=frame_index_slice,
                variable="gradients",
            )
            self._output_trajectory.write_array_fragment(
                gradient_series,
                "gradients",
                atom_indices=target_atoms,
                frame_indices=target_frames,
            )

        # get the Frame index
        for frame_index, target_index in zip(
            frame_index_group, target_frame_list, strict=True
        ):
            charges = self.trajectory.charges(frame_index)
            new_charges = np.zeros(len(atom_index_group))
            for number, at_index in enumerate(atom_index_group):
                try:
                    q = self.configuration["atom_charges"]["charges"][at_index]
                except KeyError:
                    q = charges[at_index]
                new_charges[number] = q
            self._output_trajectory.write_charges(
                new_charges, target_index, atom_indices=target_atoms
            )

        if chunk_index:
            return index, None

        unit_cell_frames = []
        unit_cell_list = []
        for frame_index, target_index in zip(
            frame_index_group, target_frame_list, strict=True
        ):
            unit_cell = self.trajectory.unit_cell(frame_index)
            if unit_cell is None:
                continue
            unit_cell_frames.append(target_index)
            unit_cell_list.append(unit_cell.direct)
        if unit_cell_frames:
            unit_cell_data = np.array(unit_cell_list)
            self._output_trajectory.write_array_fragment(
                unit_cell_data,
                "unit_cell",
                atom_indices=target_atoms,
                frame_indices=unit_cell_frames,
            )

        time = self.trajectory.time()[frame_index_group]
        self._output_trajectory.write_array_fragment(
            time, "time", atom_indices=target_atoms, frame_indices=target_frames
        )

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
