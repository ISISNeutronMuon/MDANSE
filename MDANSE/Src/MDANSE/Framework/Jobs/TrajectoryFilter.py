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
from typing import TYPE_CHECKING

import h5py
import numpy as np
from more_itertools import always_iterable

from MDANSE.Chemistry.ChemicalSystem import (
    ChemicalSystem,
    assign_molecules_after_atom_selection,
)
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    CorrelationWindow,
    Filter,
    FrameSelect,
    InstrumentResolution,
    MDANSEResult,
    MDANSETrajectory,
    OutputTrajectory,
    Projection,
    RunningMode,
    Weights,
)
from MDANSE.Mathematics.Signal import FILTER_MAP
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
    _Configuration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

if TYPE_CHECKING:
    from MDANSE.Mathematics.Signal import Filter as SFilter


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
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        transmutation="atom_transmutation",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    pps_input_file = MDANSEResult[h5py.File | None](
        label="MDANSE Position Power Spectrum",
        optional=True,
        choices=("pps/axes/romega", "/pps/isotropic/total"),
        default=None,
    )
    trajectory_filter = Filter(depends={"frames": "frames"})
    atom_selection = AtomSelection(
        depends={"trajectory": "trajectory"},
        default={"0": {"function_name": "select_all", "operation_type": "union"}},
    )
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    weights = Weights(default="atomic_weight", depends={"trajectory": "trajectory"})
    output_files = OutputTrajectory()

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.numberOfSteps = len(self.trajectory.atom_indices)

        self._atoms = self.trajectory.atom_names

        self._selected_atoms = list(
            always_iterable(self.trajectory.selection_getter(self._atoms))
        )

        # This stores the trajectory (position array) of atoms by x, y, z component, to be filtered
        self.atomic_trajectory_array = np.zeros(
            (len(self._selected_atoms), 3, len(self.frames))
        )

        self.filter = self.trajectory_filter.filter

    def run_step(self, index: int) -> tuple[int, None]:
        """Run the filter for a single atom.

        Parameters
        ----------
        index : int
            The index of the step.

        Returns
        -------
        int
            Index of step
        None
            Dummy

        """
        trajectory = self.trajectory

        # get atom index
        atom_index = self.trajectory.atom_indices[index]

        series = trajectory.read_atomic_trajectory(
            atom_index,
            first=self.frames.index_start,
            last=self.frames.index_stop + 1,
            step=self.frames.index_step,
        )

        self.atomic_trajectory_array[index] = series.T

        return index, None

    def combine(self, _index: int, _x: None):
        """Do nothing.

        Included for compatibility with the IJob workflow.

        Parameters
        ----------
        index : int
            The index of the step.
        x : any
            The returned result(s) of run_step

        """
        pass

    def finalize(self):
        """Write out the new trajectory."""
        # Get filter class and instantiate filter object

        trajectories = copy.deepcopy(self.atomic_trajectory_array)

        # Magnitude of zero frequency in filter response (equivalent to the average atomic positions)
        zero_magnitude = np.abs(self.filter.freq_response.magnitudes[0])

        # Apply filter (only apply initial position offset to atoms if filter response f(0) != 1)
        filtered_coords = apply(
            self.filter,
            trajectories,
            apply_offsets=not np.isclose(zero_magnitude, 1),
        )

        # Create new chemical system for output trajectory
        name = self.output_files.path.stem

        if not isinstance(name, str):
            name = "filtered_traj_chemical_system"
        output_chemical_system = ChemicalSystem(name)
        output_chemical_system.initialise_atoms(self._selected_atoms)
        assign_molecules_after_atom_selection(
            self.trajectory.atom_indices,
            self.trajectory.chemical_system,
            output_chemical_system,
        )

        # Create trajectory writer object
        self._output_trajectory = TrajectoryWriter(
            self.output_files.path,
            output_chemical_system,
            len(self.trajectory),
            None,
            positions_dtype=self.output_files.dtype,
            compression=self.output_files.compression,
        )

        # Write trajectory
        write_filtered_trajectory(
            parent_configuration=self,
            nsteps=len(self.frames),
            filtered_coordinates=filtered_coords,
            output_trajectory=self._output_trajectory,
        )

        for out_frame, in_frame in enumerate(self.frames):
            self._output_trajectory.write_charges(
                self.trajectory.charges(in_frame.ind)[self.trajectory.atom_indices],
                out_frame,
            )

        # The input trajectory is closed.
        self.trajectory.close()

        # The output trajectory is closed.
        write_metadata(self, self._output_trajectory._h5_file)
        self._output_trajectory.close()

        # Write the filter metadata to output
        outputFile = h5py.File(self.output_files.path, "r+")
        outputFile.create_group("metadata/filter").create_dataset(
            "trajectory_filter",
            (1,),
            data=str(self.filter),
            dtype=h5py.string_dtype(),
        )

        outputFile.close()

        super().finalize()


def apply(filter: SFilter, trajectories: np.ndarray, apply_offsets: bool) -> np.ndarray:
    """Apply the filter to the atomic trajectories.

    Parameter
    ---------
    filter : SFilter
        The filter object to be applied.
    trajectories : np.ndarray
        Atomic trajectories array with shape (num atoms, 3, num timesteps).
    apply_offsets : bool
        If true, we apply an offset to the atomic positions post-filter, representing
        a correction to preserve initial position.

    Returns
    -------
    np.ndarray
        Filtered atomic trajectories.

    """
    output_trajectory_array = np.zeros(trajectories.shape)

    for at, (x, y, z) in enumerate(trajectories):
        for i, component in enumerate((x, y, z)):
            output = filter.apply(component)

            if apply_offsets:
                offset = component[0] - output[0]
                output += offset
            output_trajectory_array[at][i] = output

    return output_trajectory_array


def write_filtered_trajectory(
    parent_configuration: TrajectoryFilter,
    nsteps: int,
    filtered_coordinates: np.ndarray,
    output_trajectory: TrajectoryWriter,
) -> None:
    """Write the filtered trajectory object.

    Parameters
    ----------
    parent_configuration : _Configuration
        Parent configuration.
    nsteps : int
        Number of simulation steps.
    filtered_coordinates : np.ndarray
        Coordinates of the filtered atomic trajectories.
    output_trajectory : TrajectoryWriter
        Trajectory writer object to write the output trajectory.

    """
    dt = parent_configuration.frames.time_step
    for index in range(nsteps):
        frame_coordinates = [
            (x[index], y[index], z[index]) for (x, y, z) in filtered_coordinates
        ]

        # The filtered configuration coordinates at the current frame index
        filtered_configuration_coordinates = np.array(frame_coordinates)

        filtered_configuration = get_output_configuration(
            parent=parent_configuration.trajectory.configuration(
                parent_configuration.frames[0].ind,
            ),
            output_chemical_system=output_trajectory.chemical_system,
            output_coordinates=filtered_configuration_coordinates,
        )

        output_trajectory.chemical_system.configuration = filtered_configuration

        output_trajectory.dump_configuration(
            filtered_configuration,
            dt * index,
            units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
        )


def get_output_configuration(
    parent: _Configuration,
    output_chemical_system: ChemicalSystem,
    output_coordinates: np.ndarray,
):
    """Return a configuration for filtered trajectory writer.

    Configuration type depends on the periodicity of the parent configuration.

    Parameters
    ----------
    parent : _Configuration
        Parent configuration.
    output_chemical_system : ChemicalSystem
        Chemical system of the output trajectory.
    output_coordinates : np.ndarray
        Output atomic coordinates.

    Returns
    -------
    RealConfiguration | PeriodicRealConfiguration
        Output configuration for the trajectory.

    """
    if parent.is_periodic:
        return PeriodicRealConfiguration(
            output_chemical_system,
            output_coordinates,
            parent.unit_cell,
        )

    return RealConfiguration(output_chemical_system, output_coordinates)
