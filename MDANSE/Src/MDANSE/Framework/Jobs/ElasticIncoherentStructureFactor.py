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

from typing import TYPE_CHECKING

import numpy as np

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atom_indices_precalculated

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.MemoryConfigurator import MemoryConfigurator


def eisf_memory_per_atom(
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
    vector_config = mem_conf.configurable[mem_conf.dependencies["q_vectors"]]
    n_dimensions = 3
    n_frames = frame_config["number"]
    n_vectors = vector_config["parameters"].get("n_vectors", 1)
    data_size = 8
    chunk_size = trajectory.chunk_size(array_name="position")
    prefactor = 4 * n_frames * n_vectors * n_dimensions * data_size / 2**20
    return (prefactor, chunk_size * prefactor, n_atoms * prefactor)


@IJob.register("ElasticIncoherentStructureFactor")
class ElasticIncoherentStructureFactor(IJob):
    """Calculates the Elastic Incoherent Structure Factor of a trajectory.

    The Elastic Incoherent Structure Factor (EISF) is defined as the limit of the
    incoherent intermediate scattering function for infinite time.

    The EISF appears as the incoherent amplitude of the elastic line in the neutron
    scattering spectrum. Elastic scattering is only present for systems in which
    the atomic motion is confined in space, as in solids. The Q-dependence of the
    EISF indicates e.g. the fraction of static/mobile atoms and the spatial dependence
    of the dynamics.
    """

    label = "Elastic Incoherent Structure Factor"

    # The category of the analysis.
    category = (
        "Analysis",
        "Scattering",
    )
    PREDICTORS = (
        "q_vectors",
        "memory",
        "running_mode",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
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
    settings["memory"] = (
        "MemoryConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "frames": "frames",
                "q_vectors": "q_vectors",
            },
            "mem_function": eisf_memory_per_atom,
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

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self._nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration["frames"]["number"]

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

        self._outputData.add(
            "eisf/axes/q",
            "LineOutputVariable",
            self.configuration["q_vectors"]["shells"],
            units="1/nm",
        )

        for element in self.trajectory.unique_names:
            self._outputData.add(
                f"eisf/{element}",
                "LineOutputVariable",
                (self._nQShells,),
                axis="eisf/axes/q",
                units="au",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "eisf/total",
            "LineOutputVariable",
            (self._nQShells,),
            axis="eisf/axes/q",
            units="au",
            main_result=True,
        )

        self._atoms = self.trajectory.atom_names

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. atomicEISF (np.array): The atomic elastic incoherent structure factor
        """

        # get atom index
        atom_index_group = self.grouped_indices[index]
        n_atoms = len(atom_index_group)

        series = self.trajectory.read_atomic_trajectory_many(
            atom_index_group,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        series = self.configuration["projection"]["projector"](series)

        atomicEISF = np.zeros((self._nQShells, n_atoms), dtype=np.float64)

        for i, q in enumerate(self.configuration["q_vectors"]["shells"]):
            if self.configuration["q_vectors"]["value"][q] is None:
                atomicEISF[i, :] = np.nan
                continue

            qVectors = self.configuration["q_vectors"]["value"][q]["q_vectors"]
            qvec_weights = self.configuration["q_vectors"]["value"][q]["weights"]

            a = np.average(
                np.swapaxes(
                    np.exp(1j * np.dot(qVectors.T, np.swapaxes(series, 1, 2))), 0, 1
                ),
                axis=0,
            )
            a = np.abs(a) ** 2

            atomicEISF[i, :] = np.average(a, axis=0, weights=qvec_weights)

        return index, atomicEISF

    def combine(self, step_index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        atom_index_group = self.grouped_indices[step_index]
        # The symbol of the atom.
        for arr_index, at_index in enumerate(atom_index_group):
            element = self._atoms[at_index]

            self._outputData[f"eisf/{element}"] += x[:, arr_index]

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """

        self.configuration["q_vectors"]["generator"].write_vectors_to_file(
            self._outputData
        )

        nAtomsPerElement = self.trajectory.get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"eisf/{element}"][:] /= number

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
        assign_weights(self._outputData, weight_dict, "eisf/%s", self.labels)

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = n_selected / n_total

        self._outputData["eisf/total"][:] = (
            weighted_sum(self._outputData, "eisf/%s", self.labels) / fact
        )
        self._outputData["eisf/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "eisf",
            "LineOutputVariable",
            axis="eisf/axes/q",
            units="au",
            main_result=True,
            partial_result=True,
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
