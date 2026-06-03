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
from scipy import fft

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atom_indices


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

        self._using_lattice_vectors = self.configuration["q_vectors"]["is_lattice"]
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

        if self._using_lattice_vectors:
            series = self.trajectory.coordinates(
                slice(
                    self.configuration["frames"]["first"],
                    self.configuration["frames"]["last"] + 1,
                    self.configuration["frames"]["step"],
                ),
                atom_index_group,
            )
        else:
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
            rho = (
                np.exp(1j * np.dot(qVectors.T, np.swapaxes(series, 1, 2)))
                * np.sqrt(qvec_weights)[:, None, None]
            )
            rho = np.swapaxes(rho, 0, 1)
            fast_len = fft.next_fast_len(rho.shape[0])
            v = fft.fft(rho, n=fast_len, axis=0)
            w = fft.fft(rho[:n_configs], n=fast_len, axis=0)
            res = fft.ifft(np.sum(v * w.conj(), axis=1), axis=0)[: self._nFrames]
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
