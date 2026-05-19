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

import numpy as np
from scipy.signal import correlate

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MolecularDynamics.Trajectory import Trajectory

CHUNK_SIZE_LIMIT = 2**29  # 512 MB memory limit per process for now


def group_atom_indices(
    traj_instance: Trajectory,
    n_proc: int = 1,
    memory_scale_factor: int = 10,
    size_limit: int = CHUNK_SIZE_LIMIT,
) -> list[list[int]]:
    """Create groups of atom indices coaligned with the chunk size in the input file.

    This function is meant to group indices so that a single process loads data
    from a single chunk per frame. Additionally, indices will be split into smaller
    sets if a process is expected to use more memory than the specified limits, or
    if there are less index sets than there are worker processes.

    Typically, the memory requirements will be proportional to the size of the
    input array, but larger. For example, DISF analysis allocates an array
    of the size of N_ATOMSxN_VECTORS, which means that the worker process
    will need significantly more memory that the size of the input coordinate
    array.

    Parameters
    ----------
    traj_instance : Trajectory
        The current input trajectory.
    n_proc : int, optional
        Number of available CPU cores or worker processes, by default 1
    memory_scale_factor : int, optional
        Multiplier of the expected memory requirements of the job, by default 10
    size_limit : int, optional
        Limit of memory per worker process, by default CHUNK_SIZE_LIMIT

    Returns
    -------
    list[list[int]]
        _description_
    """
    selected_indices = sorted(traj_instance.atom_indices)
    total_dimensions = traj_instance.variable("position").shape
    chunk_size = traj_instance.chunk_size(array_name="position")
    if chunk_size < 0:
        max_chunk_size = size_limit // (
            total_dimensions[0] * 3 * 8 * memory_scale_factor
        )
        chunk_limits = np.array([0, total_dimensions[1]])
    else:
        predicted_memory = (
            total_dimensions[0] * chunk_size * 3 * 8 * memory_scale_factor
        )
        downscale_factor = np.ceil(predicted_memory / size_limit)
        max_chunk_size = chunk_size // downscale_factor
        chunk_limits = np.concatenate(
            [np.arange(0, total_dimensions[1], chunk_size), [total_dimensions[1]]]
        )
    min_chunk_count = n_proc
    initial_sets = [
        sorted(
            set(range(chunk_limits[n], chunk_limits[n + 1])).intersection(
                selected_indices
            )
        )
        for n in range(len(chunk_limits) - 1)
    ]
    return balance_index_groups(
        initial_sets, max_size=max_chunk_size, min_count=min_chunk_count
    )


def single_sweep(index_sets: list[set[int]], max_size: int) -> list[set[int]]:
    """Check the size of each atom index set and split those exceeding the size limit.

    Parameters
    ----------
    index_sets : list[set[int]]
        List of atom index sets to be used by worker processes.
    max_size : int
        Maximum number of atoms per set.

    Returns
    -------
    list[set[int]]
        List of index sets after splitting into smaller sets.
    """
    result = []
    for ind_set in index_sets:
        set_len = len(ind_set)
        if set_len < max_size:
            result.append(ind_set)
            continue
        result.append(ind_set[: set_len // 2])
        result.append(ind_set[set_len // 2 :])
    return result


def balance_index_groups(
    index_sets: list[set[int]], max_size: int, min_count: int
) -> list[set[int]]:
    """Iteratively split atom index sets until the optimal size has been reached.

    Parameters
    ----------
    index_sets : list[set[int]]
        List of atom index set, one set per analysis step.
    max_size : int
        Maximum number of atoms per set.
    min_count : int
        Minimum number of sets needed by the analysis.

    Returns
    -------
    list[set[int]]
        List of index sets after splitting into smaller sets.
    """
    while any(len(ind_set) > max_size for ind_set in index_sets):
        index_sets = single_sweep(index_sets, max_size)
        if len(index_sets) < min_count:
            max_size = 3 * max_size // 4
    return index_sets


@IJob.register("DynamicIncoherentStructureFactor")
class DynamicIncoherentStructureFactor(IJob):
    r"""Computes the dynamic incoherent structure factor :math:`S_{\text{inc}}(\mathbf{q},\omega)` for a set of atoms.

    It can be compared to experimental data e.g. the quasielastic scattering due to
    diffusion processes.

    This property is derived from the self-correlation of individual atoms over time.
    While it does not require the :math:`\mathbf{q}`-vectors to be commensurate with the simulation
    box reciprocal lattice, a "lattice" vector generator should be chosen if you
    intend to combine the result with the coherent part into the total
    dynamic structure factor.
    """

    label = "Dynamic Incoherent Structure Factor"

    category = (
        "Analysis",
        "Scattering",
    )
    PREDICTORS = ("instrument_resolution", "q_vectors")

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {
            "dependencies": {"trajectory": "trajectory", "frames": "frames"},
        },
    )
    settings["q_vectors"] = (
        "QVectorsConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["projection"] = (
        "ProjectionConfigurator",
        {},
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
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "b_incoherent",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        vectors_per_shell = self.configuration["q_vectors"]["parameters"].get(
            "n_vectors", 1
        )
        n_proc = self.configuration["running_mode"].get("slots", 1)

        self.grouped_indices = group_atom_indices(
            self.trajectory, n_proc=n_proc, memory_scale_factor=vectors_per_shell
        )
        self.numberOfSteps = len(self.grouped_indices)

        self._nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration["frames"]["n_frames"]

        self._instrResolution = self.configuration["instrument_resolution"]

        self._atoms = self.trajectory.atom_names

        self._nOmegas = self._instrResolution["n_omegas"]

        self.add_ideal_results = (
            self.configuration["instrument_resolution"]["kernel"].lower() != "ideal"
        )

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        self._outputData.add(
            "disf/axes/q",
            "LineOutputVariable",
            self.configuration["q_vectors"]["shells"],
            units="1/nm",
        )

        self._outputData.add(
            "disf/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "disf/res/time_window",
            "LineOutputVariable",
            self._instrResolution["time_window"],
            units="au",
        )

        self._outputData.add(
            "disf/axes/omega",
            "LineOutputVariable",
            self._instrResolution["omega"],
            units="rad/ps",
        )
        self._outputData.add(
            "disf/res/omega_window",
            "LineOutputVariable",
            self._instrResolution["omega_window"],
            axis="disf/axes/omega",
            units="au",
        )

        for element in self.trajectory.unique_names:
            self._outputData.add(
                f"disf/f(q,t)/{element}",
                "SurfaceOutputVariable",
                (self._nQShells, self._nFrames),
                axis="disf/axes/q|disf/axes/time",
                units="au",
            )
            self._outputData.add(
                f"disf/s(q,f)/{element}",
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="disf/axes/q|disf/axes/omega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            if self.add_ideal_results:
                self._outputData.add(
                    f"disf/s(q,f)/ideal/{element}",
                    "SurfaceOutputVariable",
                    (self._nQShells, self._nOmegas),
                    axis="disf/axes/q|disf/axes/omega",
                    units="au",
                )

        self._outputData.add(
            "disf/f(q,t)/total",
            "SurfaceOutputVariable",
            (self._nQShells, self._nFrames),
            axis="disf/axes/q|disf/axes/time",
            units="au",
        )
        self._outputData.add(
            "disf/s(q,f)/total",
            "SurfaceOutputVariable",
            (self._nQShells, self._nOmegas),
            axis="disf/axes/q|disf/axes/omega",
            units="au",
            main_result=True,
        )
        if self.add_ideal_results:
            self._outputData.add(
                "disf/s(q,f)/ideal/total",
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="disf/axes/q|disf/axes/omega",
                units="au",
            )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. atomicSF (np.array): The atomic structure factor
        """

        atom_index_group = self.grouped_indices[index]
        n_atoms = len(atom_index_group)

        series = self.trajectory.read_atomic_trajectory_many(
            atom_index_group,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        series = self.configuration["projection"]["projector"](series)

        disf_per_q_shell = {}
        for q in self.configuration["q_vectors"]["shells"]:
            if self.configuration["q_vectors"]["value"][q] is None:
                disf_per_q_shell[q] = np.nan
                continue
            disf_per_q_shell[q] = np.zeros((self._nFrames, n_atoms), dtype=np.float64)

        n_configs = self.configuration["frames"]["n_configs"]
        for q in self.configuration["q_vectors"]["shells"]:
            if self.configuration["q_vectors"]["value"][q] is None:
                continue
            qVectors = self.configuration["q_vectors"]["value"][q]["q_vectors"]
            qvec_weights = self.configuration["q_vectors"]["value"][q]["weights"]
            rho = np.exp(
                1j * np.einsum("inj,jk,k->ikn", series, qVectors, np.sqrt(qvec_weights))
            )
            res = np.hstack(
                [
                    correlate(rho[:, :, n], rho[:n_configs, :, n], mode="valid")
                    for n in range(rho.shape[2])
                ]
            )
            norm = n_configs * np.sum(qvec_weights)
            res /= norm

            disf_per_q_shell[q] += res.real
        return index, disf_per_q_shell

    def combine(self, index, disf_per_q_shell):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        at_indices = self.grouped_indices[index]
        for rel_index, abs_index in enumerate(at_indices):
            element = self._atoms[abs_index]
            for i, v in enumerate(disf_per_q_shell.values()):
                if hasattr(v, "shape"):
                    self._outputData[f"disf/f(q,t)/{element}"][i, :] += v[:, rel_index]
                else:
                    self._outputData[f"disf/f(q,t)/{element}"][i, :] += v

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        self.configuration["q_vectors"]["generator"].write_vectors_to_file(
            self._outputData
        )

        nAtomsPerElement = self.trajectory.get_natoms()

        selected_weights, all_weights = self.trajectory.get_weights(
            prop=self.configuration["weights"]["property"]
        )
        for weights in selected_weights, all_weights:
            for key, value in weights.items():
                weights[key] = abs(value) ** 2
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            1,
        )
        assign_weights(self._outputData, weight_dict, "disf/f(q,t)/%s", self.labels)
        assign_weights(self._outputData, weight_dict, "disf/s(q,f)/%s", self.labels)
        if self.add_ideal_results:
            assign_weights(
                self._outputData, weight_dict, "disf/s(q,f)/ideal/%s", self.labels
            )
        for element, number in list(nAtomsPerElement.items()):
            extra_scaling = 1.0 / number
            self._outputData[f"disf/f(q,t)/{element}"] *= extra_scaling
            self._outputData[f"disf/s(q,f)/{element}"][:] = get_spectrum(
                self._outputData[f"disf/f(q,t)/{element}"],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
            )
            if self.add_ideal_results:
                self._outputData[f"disf/s(q,f)/ideal/{element}"][:] = get_spectrum(
                    self._outputData[f"disf/f(q,t)/{element}"],
                    None,
                    self.configuration["instrument_resolution"]["time_step"],
                    axis=1,
                )

        n_selected = sum(nAtomsPerElement.values())
        n_total = len(self.trajectory.atom_types)
        fact = n_selected / n_total

        self._outputData["disf/f(q,t)/total"][:] = (
            weighted_sum(self._outputData, "disf/f(q,t)/%s", self.labels) / fact
        )
        self._outputData["disf/f(q,t)/total"].scaling_factor = fact

        self._outputData["disf/s(q,f)/total"][:] = (
            weighted_sum(self._outputData, "disf/s(q,f)/%s", self.labels) / fact
        )
        self._outputData["disf/s(q,f)/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "disf/f(q,t)",
            "SurfaceOutputVariable",
            axis="disf/axes/q|disf/axes/time",
            units="au",
        )
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "disf/s(q,f)",
            "SurfaceOutputVariable",
            axis="disf/axes/q|disf/axes/omega",
            units="au",
            main_result=True,
            partial_result=True,
        )

        if self.add_ideal_results:
            self._outputData["disf/s(q,f)/ideal/total"][:] = (
                weighted_sum(self._outputData, "disf/s(q,f)/ideal/%s", self.labels)
                / fact
            )
            self._outputData["disf/s(q,f)/ideal/total"].scaling_factor = fact

            add_grouped_totals(
                self.trajectory,
                self._outputData,
                "disf/s(q,f)/ideal",
                "SurfaceOutputVariable",
                axis="disf/axes/q|disf/axes/omega",
                units="au",
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
