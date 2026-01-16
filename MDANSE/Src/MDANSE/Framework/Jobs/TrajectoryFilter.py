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

import json
import math

import h5py
import numpy as np
from more_itertools import always_iterable

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Signal import FILTER_MAP, Filter
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
    _Configuration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter


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
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "atomic_weight",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
        },
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "label": "MDANSE trajectory (filename, datatype, chunk size, compression, logfile output)",
            "format": "MDTFormat",
        },
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.chunk_size = 100
        self.n_chunks = math.ceil(
            self.configuration["frames"]["number"] / self.chunk_size
        )
        self.numberOfSteps = self.n_chunks

        self._atoms = self.trajectory.atom_names

        self._selected_atoms = list(
            always_iterable(self.trajectory.selection_getter(self._atoms))
        )

        # This stores the trajectory (position array) of atoms by x, y, z component, to be filtered
        self.atomic_trajectory_array = np.zeros(
            (len(self._selected_atoms), 3, self.chunk_size)
        )

        # Get filter class and instantiate filter object
        filter_config = json.loads(self.configuration["trajectory_filter"]["value"])
        filter_class, filter_attributes = (
            FILTER_MAP[filter_config["filter"]],
            filter_config["attributes"],
        )
        filter_attributes.setdefault(
            "n_steps", self.configuration["trajectory"]["length"]
        )
        filter_attributes.setdefault(
            "time_step_ps", self.configuration["trajectory"]["md_time_step"]
        )
        self.filter = filter_class(**filter_attributes)

        name = self.configuration["output_files"]["file"].stem
        if not isinstance(name, str):
            name = "filtered_traj_chemical_system"

        output_chemical_system = ChemicalSystem(name)
        output_chemical_system.initialise_atoms(self._selected_atoms)

        # Create trajectory writer object
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            output_chemical_system,
            filter_attributes["n_steps"],
            positions_dtype=self.configuration["output_files"]["dtype"],
            compression=self.configuration["output_files"]["compression"],
        )

    def run_step(self, index):
        """Run the filter for a single atom.

        Parameters
        ----------
        index : int
            The index of the step.

        """
        LOG.debug(f"Running step: {index}")

        self.atomic_trajectory_array.fill(0)
        for idx in range(len(self.trajectory.atom_indices)):
            atom_index = self.trajectory.atom_indices[idx]
            series = self.trajectory.read_atomic_trajectory(
                atom_index,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )
            first = index * self.chunk_size
            last = (index + 1) * self.chunk_size
            if last > self.configuration["frames"]["last"]:
                last = self.configuration["frames"]["last"] + 1
            self.atomic_trajectory_array[idx, :, : last - first] = series.T[
                :, first:last
            ]

        # Magnitude of zero frequency in filter response (equivalent to the average atomic positions)
        zero_magnitude = np.abs(self.filter.freq_response.magnitudes[0])

        # Apply filter (only apply initial position offset to atoms if filter response f(0) != 1)
        filtered_coords = apply(
            self.filter,
            self.atomic_trajectory_array,
            apply_offsets=not np.isclose(zero_magnitude, 1),
        )

        time = self.configuration["frames"]["time"]
        dt = time[1] - time[0]

        for i in range(self.chunk_size):
            j = i + index * self.chunk_size
            if j >= self.configuration["frames"]["number"]:
                break

            filtered_configuration = get_output_configuration(
                parent=self.configuration["trajectory"]["instance"].configuration(
                    self.configuration["frames"]["value"][j],
                ),
                output_chemical_system=self._output_trajectory.chemical_system,
                output_coordinates=filtered_coords[:, :, i],
            )

            self._output_trajectory.dump_configuration(
                filtered_configuration,
                dt * j,
                units={
                    "time": "ps",
                    "unit_cell": "nm",
                    "coordinates": "nm",
                },
            )

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
            data=str(filter),
            dtype=h5py.string_dtype(),
        )

        outputFile.close()

        super().finalize()


def apply(filter: Filter, trajectories: np.ndarray, apply_offsets: bool) -> np.ndarray:
    """Apply the filter to the atomic trajectories.

    Parameter
    ---------
    filter : Filter
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
