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

import copy
import json

import h5py
import numpy as np
from more_itertools import always_iterable, chunked

from MDANSE.Chemistry.ChemicalSystem import (
    ChemicalSystem,
    assign_molecules_after_atom_selection,
)
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Signal import FILTER_MAP, Filter
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.util_types import FloatArray


@IJob.register("TrajectoryFilter")
class TrajectoryFilter(IJob):
    """Design and apply a filter for the atomic trajectories.

    This job outputs a new trajectory, where part of the vibrational
    spectrum of atoms has been removed. Effectively, this allows to
    separate the high- and low-frequency vibrational modes, also in
    disordered systems where lattice-dynamics analysis would be difficult.

    The filter is applied in the standard signal-processing approach,
    where the positions of atoms as a function of time are Fourier-transformed
    (producing a position power spectrum), the filter is applied to the spectrum,
    and the modified spectrum is Fourier-transformed back into positions.
    """

    label = "Trajectory Filter"

    category = ("Trajectory",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["pps_input_file"] = (
        "HDFInputFileConfigurator",
        {
            "label": "MDANSE Position Power Spectrum",
            "default": "",
            "optional": True,
            "variables": ("pps/axes/romega", "/pps/isotropic/total"),
        },
    )
    settings["trajectory_filter"] = (
        "TrajectoryFilterConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "frames": "frames",
                "pps_input_file": "pps_input_file",
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
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "format": "MDTFormat",
        },
    )

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
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
            chunked(self.trajectory.atom_indices, atoms_per_chunk)
        )
        self.grouped_frames = list(
            chunked(
                range(
                    self.configuration["frames"]["first"],
                    self.configuration["frames"]["last"] + 1,
                    self.configuration["frames"]["step"],
                ),
                frames_per_chunk,
            )
        )
        self.numberOfSteps = len(self.grouped_indices)
        self.n_atom_chunks = len(self.grouped_indices)
        self.n_frame_chunks = n_time_steps
        self.atoms_per_chunk = atoms_per_chunk
        self.frames_per_chunk = frames_per_chunk

        filter_config = json.loads(self.configuration["trajectory_filter"]["value"])

        filter_class, filter_attributes = (
            FILTER_MAP[filter_config["filter"]],
            filter_config["attributes"],
        )

        filter_attributes.setdefault("n_steps", self.configuration["frames"]["number"])
        filter_attributes.setdefault(
            "time_step_ps", self.configuration["frames"]["time_step"]
        )

        self.filter = filter_class(
            **filter_attributes
        )  # Create trajectory writer object

        # Create new chemical system for output trajectory
        name = self.configuration["output_files"]["file"].stem
        if not isinstance(name, str):
            name = "filtered_traj_chemical_system"
        output_chemical_system = ChemicalSystem(name)
        output_chemical_system.initialise_atoms(
            list(
                always_iterable(
                    self.trajectory.selection_getter(self.trajectory.atom_types)
                )
            ),
            list(
                always_iterable(
                    self.trajectory.selection_getter(self.trajectory.atom_names)
                )
            ),
        )
        assign_molecules_after_atom_selection(
            self.trajectory.atom_indices,
            self.trajectory.chemical_system,
            output_chemical_system,
        )

        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            output_chemical_system,
            self.configuration["frames"]["number"],
            selected_atoms=None,
            positions_dtype=self.configuration["output_files"]["dtype"],
            compression=self.configuration["output_files"]["compression"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            meta_block_size=self.configuration["output_files"]["meta_block_size"],
        )

    def run_step(self, index):
        """Run the filter for a single atom.

        Parameters
        ----------
        index : int
            The index of the step.

        """
        trajectory = self.trajectory

        # get atom index
        atom_indices = self.grouped_indices[index]

        series = trajectory.read_atomic_trajectory_many(
            atom_indices,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        # Magnitude of zero frequency in filter response (equivalent to the average atomic positions)
        zero_magnitude = np.abs(self.filter.freq_response.magnitudes[0])

        # Apply filter (only apply initial position offset to atoms if filter response f(0) != 1)
        filtered_coords = apply(
            self.filter,
            series,
            apply_offsets=not np.isclose(zero_magnitude, 1),
        )

        return index, filtered_coords

    def combine(self, index: int, x: None):
        """Do nothing.

        Included for compatibility with the IJob workflow.

        Parameters
        ----------
        index : int
            The index of the step.
        x : any
            The returned result(s) of run_step

        """
        atom_indices = self.grouped_indices[index]
        self._output_trajectory.write_array_fragment(
            x,
            "coordinates",
            atom_indices=atom_indices,
        )
        if index:
            return

        target_frames = chunked(range(self.number_of_frames), self.frames_per_chunk)
        for frame_index_group in self.grouped_frames:
            unit_cell_frames = []
            unit_cell_list = []
            target_frame_list = next(target_frames)
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
                    frame_indices=unit_cell_frames,
                )

            time = self.trajectory.time()[frame_index_group]
            self._output_trajectory.write_array_fragment(
                time, "time", frame_indices=target_frame_list
            )

    def finalize(self):
        """Write out the new trajectory."""
        # Get filter class and instantiate filter object

        for out_frame, in_frame in enumerate(
            range(
                self.configuration["frames"]["first"],
                self.configuration["frames"]["last"] + 1,
                self.configuration["frames"]["step"],
            )
        ):
            self._output_trajectory.write_charges(
                self.trajectory.charges(in_frame)[self.trajectory.atom_indices],
                out_frame,
            )

        # The input trajectory is closed.
        self.trajectory.close()

        # The output trajectory is closed.
        write_metadata(self, self._output_trajectory._h5_file)
        self._output_trajectory.close()

        # Write the filter metadata to output
        outputFile = h5py.File(self.configuration["output_files"]["file"], "r+")
        outputFile.create_group("metadata/filter").create_dataset(
            "trajectory_filter",
            (1,),
            data=str(self.filter),
            dtype=h5py.string_dtype(),
        )

        outputFile.close()

        super().finalize()


def apply(filter: Filter, trajectories: FloatArray, apply_offsets: bool) -> FloatArray:
    """Apply the filter to the atomic trajectories.

    Parameter
    ---------
    filter : Filter
        The filter object to be applied.
    trajectories : FloatArray
        Atomic trajectories array with shape (num atoms, 3, num timesteps).
    apply_offsets : bool
        If true, we apply an offset to the atomic positions post-filter, representing
        a correction to preserve initial position.

    Returns
    -------
    FloatArray
        Filtered atomic trajectories.

    """
    output = filter.apply(trajectories)
    if apply_offsets:
        output += trajectories[:1] - output[:1]
    return output
