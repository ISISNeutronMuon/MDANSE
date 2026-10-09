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

import abc
import itertools as it
from typing import TYPE_CHECKING

from scipy import fft

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atom_indices_precalculated

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.MemoryConfigurator import MemoryConfigurator


def ccorr_memory_per_atom(
    mem_conf: MemoryConfigurator, n_atoms: int = 1
) -> tuple[int, int, int]:
    """Calculate the memory requirements of a DISF calculation.

    The data size is fixed as 8 bytes per number, since the arrays allocated
    by numpy in this analysis are most likely going to be float64, even
    if the coordinates in the input trajectory are float32.

    Parameters
    ----------
    mem_conf : MemoryConfigurator
        The configurator instance which contains the needed inputs
    n_atoms : int, optional
        Use a specific number of atoms in the calculation, by default 1

    Returns
    -------
    tuple[int, int int]
        MB per atom, per chunk and per n_atoms from input, respectively
    """
    trajectory = mem_conf.configurable[mem_conf.dependencies["trajectory"]]["instance"]
    frame_config = mem_conf.configurable[mem_conf.dependencies["frames"]]
    n_dimensions = 3
    n_frames = frame_config["number"]
    corr_frames = frame_config["n_frames"]
    data_size = 8
    chunk_size = trajectory.chunk_size(array_name="position")
    prefactor = 8 * (n_frames + corr_frames) * n_dimensions * data_size / 2**20
    return (prefactor, chunk_size * prefactor, n_atoms * prefactor)


class CartesianCorrelationFunction(IJob):
    enabled = False
    visible = False

    category = (
        "Analysis",
        "Dynamics",
    )
    PREDICTORS = (
        "frames",
        "memory",
        "running_mode",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
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
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            }
        },
    )
    settings["memory"] = (
        "MemoryConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "frames": "frames",
            },
            "mem_function": ccorr_memory_per_atom,
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = (
        "RunningModeConfigurator",
        {
            "dependencies": {
                "memory": "memory",
            }
        },
    )

    CF_NAME = ""
    CF_UNITS = ""
    MAIN_RESULTS = ""

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        n_proc = self.configuration["running_mode"].get("slots", 1)

        self.grouped_indices = group_atom_indices_precalculated(
            self.trajectory,
            self.configuration["frames"]["number"],
            n_proc=n_proc,
            max_group_size=self.configuration["memory"]["atoms_per_step"][0],
        )
        self.numberOfSteps = len(self.grouped_indices)

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        self.n_frames = self.configuration["frames"]["n_frames"]

        selected_weights, all_weights = self.trajectory.get_weights(
            prop=self.configuration["weights"]["property"]
        )
        if self.configuration["weights"]["property"] in ("b_coherent", "b_incoherent"):
            for weights in selected_weights, all_weights:
                for key, value in weights.items():
                    weights[key] = abs(value) ** 2
        self.weight_dict = get_weights(
            selected_weights,
            all_weights,
            self.trajectory.get_natoms(),
            self.trajectory.get_all_natoms(),
            1,
        )

        self.initialize_outputdata()

    def initialize_outputdata(self):
        self._outputData.add(
            f"{self.CF_NAME}/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._cf_components = ["isotropic"]
        for i, j in it.combinations_with_replacement(["x", "y", "z"], 2):
            self._cf_components.append(f"{i}{j}")

        for component in self._cf_components:
            for result in [*list(self.trajectory.unique_names), "total"]:
                main_result = f"{self.CF_NAME}/{component}/" == self.MAIN_RESULTS
                partial_result = main_result and result != "total"
                self._outputData.add(
                    f"{self.CF_NAME}/{component}/{result}",
                    "LineOutputVariable",
                    (self.configuration["frames"]["n_frames"],),
                    axis=f"{self.CF_NAME}/axes/time",
                    units=self.CF_UNITS,
                    main_result=main_result,
                    partial_result=partial_result,
                )

    @abc.abstractmethod
    def get_series(self, index):
        pass

    def run_step(self, index):
        series = self.get_series(index)

        u_x = series[:, :, 0]
        u_y = series[:, :, 1]
        u_z = series[:, :, 2]

        n_configs = self.configuration["frames"]["n_configs"]
        cfs = []
        for u_i, u_j in it.combinations_with_replacement([u_x, u_y, u_z], 2):
            fast_len = fft.next_fast_len(len(u_i))
            v = fft.fft(u_i, n=fast_len, axis=0)
            w = fft.fft(u_j[:n_configs], n=fast_len, axis=0)
            single_corr = fft.ifft(v * w.conj(), axis=0)[: self.n_frames] / n_configs
            cfs.append(single_corr.real)
        return index, cfs

    def combine(self, step_index, cfs):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        # The symbol of the atom.
        atom_index_group = self.grouped_indices[step_index]
        isotropic = (cfs[0] + cfs[3] + cfs[5]) / 3
        # The symbol of the atom.
        for arr_index, at_index in enumerate(atom_index_group):
            element = self.trajectory.atom_names[at_index]

            self._outputData[f"{self.CF_NAME}/isotropic/{element}"] += isotropic[
                :, arr_index
            ]

            for i, (j, k) in enumerate(
                it.combinations_with_replacement(["x", "y", "z"], 2)
            ):
                self._outputData[f"{self.CF_NAME}/{j}{k}/{element}"] += cfs[i][
                    :, arr_index
                ]

    def weight_and_group(self):
        nAtomsPerElement = self.trajectory.get_natoms()
        fact = sum(nAtomsPerElement.values()) / len(self.trajectory.atom_types)

        for component in self._cf_components:
            for element, number in nAtomsPerElement.items():
                self._outputData[f"{self.CF_NAME}/{component}/{element}"][:] /= number

            assign_weights(
                self._outputData,
                self.weight_dict,
                f"{self.CF_NAME}/{component}/%s",
                self.labels,
            )

            self._outputData[f"{self.CF_NAME}/{component}/total"][:] = (
                weighted_sum(
                    self._outputData, f"{self.CF_NAME}/{component}/%s", self.labels
                )
                / fact
            )
            self._outputData[f"{self.CF_NAME}/{component}/total"].scaling_factor = fact

            add_grouped_totals(
                self.trajectory,
                self._outputData,
                f"{self.CF_NAME}/{component}",
                "LineOutputVariable",
                axis=f"{self.CF_NAME}/axes/time",
                units=self.CF_UNITS,
                main_result=f"{self.CF_NAME}/{component}/" == self.MAIN_RESULTS,
                partial_result=f"{self.CF_NAME}/{component}/" == self.MAIN_RESULTS,
            )

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        self.weight_and_group()

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
