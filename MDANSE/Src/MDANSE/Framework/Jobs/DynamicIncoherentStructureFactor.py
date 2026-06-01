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

import numpy as np
from scipy.signal import correlate

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    CorrelationWindow,
    FrameSelect,
    GroupingLevel,
    InstrumentResolution,
    MDANSETrajectory,
    OutputFile,
    Projection,
    QVectors,
    RunningMode,
    Weights,
)
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum


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

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        grouping="grouping_level",
        transmutation="atom_transmutation",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    instrument_resolution = InstrumentResolution(
        depends={"trajectory": "trajectory", "window": "frame_window"},
    )
    q_vectors = QVectors(depends={"trajectory": "trajectory"})
    projection = Projection()
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    weights = Weights(default="b_incoherent", depends={"trajectory": "trajectory"})
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.generator = self.q_vectors.generator
        self.generator.generate()
        self.numberOfSteps = len(self.trajectory.atom_indices)
        self._nQShells = len(self.generator.q_vectors)
        self._nFrames = self.frame_window.n_frames
        self._atoms = self.trajectory.atom_names
        self.resolution = self.instrument_resolution.run_resolution

        self._nOmegas = self.resolution.n_omegas

        self.add_ideal_results = self.resolution.add_ideal

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        self._outputData.add(
            "disf/axes/q",
            "LineOutputVariable",
            self.generator.shells,
            units="1/nm",
        )

        self._outputData.add(
            "disf/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )
        self._outputData.add(
            "disf/res/time_window",
            "LineOutputVariable",
            self.resolution.time_window,
            units="au",
        )

        self._outputData.add(
            "disf/axes/omega",
            "LineOutputVariable",
            self.resolution.omega,
            units="rad/ps",
        )
        self._outputData.add(
            "disf/res/omega_window",
            "LineOutputVariable",
            self.resolution.omega_window,
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

        atom_index = self.trajectory.atom_indices[index]

        series = self.trajectory.read_atomic_trajectory(
            atom_index,
            first=self.frames.index_start,
            last=self.frames.index_stop + 1,
            step=self.frames.index_step,
        )

        series = self.projection.projector(series)

        disf_per_q_shell = {
            q: np.zeros((self._nFrames,), dtype=np.float64)
            for q in self.generator.q_vectors
        }

        n_configs = self.frame_window.n_configs
        for q in self.generator.q_vectors:
            if self.generator.q_vectors[q] is None:
                continue
            qVectors = self.generator.q_vectors[q]["q_vectors"]

            rho = np.exp(1j * np.dot(series, qVectors))
            res = correlate(rho, rho[:n_configs], mode="valid").T[0] / (
                n_configs * rho.shape[1]
            )

            disf_per_q_shell[q] += res.real

        return index, disf_per_q_shell

    def combine(self, index, disf_per_q_shell):
        """
        Combines returned results of run_step.

        Parameters
        ----------
        index : int
            The index of the step.
        x : Any
            The returned result(s) of run_step.
        """

        element = self._atoms[self.trajectory.atom_indices[index]]
        for i, v in enumerate(disf_per_q_shell.values()):
            self._outputData[f"disf/f(q,t)/{element}"][i, :] += v

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        self.generator.write_vectors_to_file(self._outputData)

        nAtomsPerElement = self.trajectory.get_natoms()

        selected_weights, all_weights = self.trajectory.get_weights(prop=self.weights)

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
                self._outputData,
                weight_dict,
                "disf/s(q,f)/ideal/%s",
                self.labels,
            )
        for element, number in list(nAtomsPerElement.items()):
            extra_scaling = 1.0 / number
            self._outputData[f"disf/f(q,t)/{element}"] *= extra_scaling
            self._outputData[f"disf/s(q,f)/{element}"][:] = get_spectrum(
                self._outputData[f"disf/f(q,t)/{element}"],
                self.resolution.time_window,
                self.frames.time_step,
                axis=1,
            )
            if self.add_ideal_results:
                self._outputData[f"disf/s(q,f)/ideal/{element}"][:] = get_spectrum(
                    self._outputData[f"disf/f(q,t)/{element}"],
                    None,
                    self.frames.time_step,
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
            self.output_files.root,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
