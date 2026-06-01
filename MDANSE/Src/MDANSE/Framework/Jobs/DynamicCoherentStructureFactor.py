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

from math import sqrt

import numpy as np
from scipy.signal import correlate

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
    pair_labels,
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
    QVectors,
    RangeCellCutoff,
    RunningMode,
    Weights,
)
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class DynamicCoherentStructureFactorError(Exception):
    pass


class DynamicCoherentStructureFactor(IJob):
    r"""Computes the dynamic coherent structure factor :math:`S_{\text{coh}}(\mathbf{q}, \omega)` for a set of atoms.

    It can be compared to experimental data e.g. the energy-integrated, static structure
    factor :math:`S_{\text{coh}}(q)` or the dispersion and intensity of phonons.

    The coherent part is derived from correlations between pairs of atoms.
    This analysis requires the :math:`\mathbf{q}`-vectors to be commensurate
    with the reciprocal lattice of the simulation box.
    """

    label = "Dynamic Coherent Structure Factor"

    category = (
        "Analysis",
        "Scattering",
    )
    PREDICTORS = ("instrument_resolution", "q_vectors")

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        transmutation="atom_transmutation",
        grouping="grouping_level",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    q_vectors = QVectors(depends={"trajectory": "trajectory"})
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    instrument_resolution = InstrumentResolution(
        depends={"trajectory": "trajectory", "window": "frame_window"},
    )
    weights = Weights(default="b_coherent", depends={"trajectory": "trajectory"})
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.generator: IQVectors = self.q_vectors.generator
        self.generator.generate()
        self.numberOfSteps = self.generator.n_shells

        nQShells = self.generator.n_shells
        if not isinstance(
            self.generator,
            LatticeQVectors,
        ):
            LOG.warning(
                "This task should be used with a lattice-based Q vector generator. "
                "You have picked {type(self.generator.__name__}}. "
                "The results are likely to be incorrect."
            )

        self._nFrames = self.frame_window.n_frames

        self.resolution = self.instrument_resolution.run_resolution
        self._nOmegas = self.resolution.n_omegas

        self._outputData.add(
            "dcsf/axes/q",
            "LineOutputVariable",
            self.generator.shells,
            units="1/nm",
        )

        self._outputData.add(
            "dcsf/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )
        self._outputData.add(
            "dcsf/res/time_window",
            "LineOutputVariable",
            self.resolution.time_window,
            units="au",
        )

        self._outputData.add(
            "dcsf/axes/omega",
            "LineOutputVariable",
            self.resolution.omega,
            units="rad/ps",
        )
        self._outputData.add(
            "dcsf/res/omega_window",
            "LineOutputVariable",
            self.resolution.omega_window,
            axis="dcsf/axes/omega",
            units="au",
        )

        self.indices_per_element = self.trajectory.get_indices()

        self.labels = pair_labels(
            self.trajectory,
        )

        for pair_str, _ in self.labels:
            self._outputData.add(
                f"dcsf/f(q,t)/{pair_str}",
                "SurfaceOutputVariable",
                (nQShells, self._nFrames),
                axis="dcsf/axes/q|dcsf/axes/time",
                units="au",
            )
            self._outputData.add(
                f"dcsf/s(q,f)/{pair_str}",
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="dcsf/axes/q|dcsf/axes/omega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            if self.resolution.add_ideal:
                self._outputData.add(
                    f"dcsf/s(q,f)/ideal/{pair_str}",
                    "SurfaceOutputVariable",
                    (nQShells, self._nOmegas),
                    axis="dcsf/axes/q|dcsf/axes/omega",
                    units="au",
                )

        self._outputData.add(
            "dcsf/f(q,t)/total",
            "SurfaceOutputVariable",
            (nQShells, self._nFrames),
            axis="dcsf/axes/q|dcsf/axes/time",
            units="au",
        )
        self._outputData.add(
            "dcsf/s(q,f)/total",
            "SurfaceOutputVariable",
            (nQShells, self._nOmegas),
            axis="dcsf/axes/q|dcsf/axes/omega",
            units="au",
            main_result=True,
        )
        if self.resolution.add_ideal:
            self._outputData.add(
                "dcsf/s(q,f)/ideal/total",
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="dcsf/axes/q|dcsf/axes/omega",
                units="au",
            )

        self._cell_std = 0.0
        try:
            all_cells = [
                self.trajectory.unit_cell(frame.ind)._unit_cell for frame in self.frames
            ]
        except TypeError:
            self._average_unit_cell = None
        else:
            self._average_unit_cell = UnitCell(
                np.mean(
                    all_cells,
                    axis=0,
                ),
            )
            self._cell_std = UnitCell(
                np.std(
                    all_cells,
                    axis=0,
                ),
            )

    def run_step(self, index: int) -> tuple[int, dict[str, np.ndarray] | None]:
        """Run the analysis for a single Q shell.

        Parameters
        ----------
        index : int
            index of the Q vector shell

        Returns
        -------
        int, np.ndarray
            shell index, rho density array

        """
        shell = self.generator.shells[index]

        if (
            shell not in self.generator.q_vectors
            or self.generator.q_vectors[shell] is None
        ):
            return index, None

        traj = self.trajectory

        nQVectors = self.generator.q_vectors[shell]["q_vectors"].shape[1]

        rho = {
            element: np.zeros(
                (len(self.frames), nQVectors),
                dtype=np.complex64,
            )
            for element in self.trajectory.unique_names
        }

        cell_present = True
        cell_fixed = True
        # loop over the trajectory time steps
        for i, frame in enumerate(self.frames):
            unit_cell = traj.unit_cell(frame.ind)

            if unit_cell is None:
                cell_present = False
            elif not np.allclose(
                unit_cell.direct,
                self._average_unit_cell.direct,
            ):
                cell_fixed = False

            if (
                cell_present
                and (hkls := self.generator.q_vectors[shell].get("hkls")) is not None
            ):
                qVectors = IQVectors.hkl_to_qvectors(hkls, unit_cell)
            else:
                qVectors = self.generator.q_vectors[shell]["q_vectors"]

            coords = traj.configuration(frame.ind)["coordinates"]

            for element, idxs in self.indices_per_element.items():
                selectedCoordinates = np.take(coords, idxs, axis=0)

                rho[element][i, :] = np.sum(
                    np.exp(1j * np.dot(selectedCoordinates, qVectors)),
                    axis=0,
                )
        if not cell_present:
            LOG.warning(
                "You are running the DCSF calculation on a trajectory without periodic boundary conditions."
            )
        if not cell_fixed:
            LOG.warning(
                f"The unit cell is VARIABLE with the standard deviation of {self._cell_std}. This analysis should not be used with NPT runs! PLEASE CHECK YOUR RESULTS CAREFULLY."
            )

        return index, rho

    def combine(self, index: int, x: np.ndarray):
        """Add partial results to the final array."""
        if x is not None:
            n_configs = self.frame_window.n_configs

            for pair_str, (label_i, label_j) in self.labels:
                # F_ab(Q,t) = F_ba(Q,t) this is valid as long as
                # n_configs is sufficiently large
                corr = correlate(x[label_i], x[label_j][:n_configs], mode="valid").T[
                    0
                ] / (n_configs * x[label_i].shape[1])
                self._outputData[f"dcsf/f(q,t)/{pair_str}"][index, :] += corr.real

    def finalize(self):
        """Apply weights and write out the results."""
        self.generator.write_vectors_to_file(self._outputData)

        nAtomsPerElement = self.trajectory.get_natoms()

        selected_weights, all_weights = self.trajectory.get_weights(prop=self.weights)
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            2,
            conc_exp=0.5,
        )
        assign_weights(self._outputData, weight_dict, "dcsf/f(q,t)/%s", self.labels)
        assign_weights(self._outputData, weight_dict, "dcsf/s(q,f)/%s", self.labels)
        if self.resolution.add_ideal:
            assign_weights(
                self._outputData, weight_dict, "dcsf/s(q,f)/ideal/%s", self.labels
            )
        for pair_str, (label_i, label_j) in self.labels:
            ni = nAtomsPerElement[label_i]
            nj = nAtomsPerElement[label_j]
            self._outputData[f"dcsf/f(q,t)/{pair_str}"] /= sqrt(ni * nj)
            self._outputData[f"dcsf/s(q,f)/{pair_str}"][:] = get_spectrum(
                self._outputData[f"dcsf/f(q,t)/{pair_str}"],
                self.resolution.time_window,
                self.frames.time_step,
                axis=1,
            )
            if self.resolution.add_ideal:
                self._outputData[f"dcsf/s(q,f)/ideal/{pair_str}"][:] = get_spectrum(
                    self._outputData[f"dcsf/f(q,t)/{pair_str}"],
                    None,
                    self.frames.time_step,
                    axis=1,
                )

        n_selected = sum(nAtomsPerElement.values())
        n_total = len(self.trajectory.atom_types)
        fact = n_selected / n_total

        self._outputData["dcsf/f(q,t)/total"][:] = (
            weighted_sum(self._outputData, "dcsf/f(q,t)/%s", self.labels) / fact
        )
        self._outputData["dcsf/f(q,t)/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "dcsf/f(q,t)",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="dcsf/axes/q|dcsf/axes/time",
            units="au",
        )

        self._outputData["dcsf/s(q,f)/total"][:] = (
            weighted_sum(self._outputData, "dcsf/s(q,f)/%s", self.labels) / fact
        )
        self._outputData["dcsf/s(q,f)/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "dcsf/s(q,f)",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="dcsf/axes/q|dcsf/axes/omega",
            units="au",
            main_result=True,
            partial_result=True,
        )

        if self.resolution.add_ideal:
            self._outputData["dcsf/s(q,f)/ideal/total"][:] = (
                weighted_sum(self._outputData, "dcsf/s(q,f)/ideal/%s", self.labels)
                / fact
            )
            self._outputData["dcsf/s(q,f)/ideal/total"].scaling_factor = fact
            add_grouped_totals(
                self.trajectory,
                self._outputData,
                "dcsf/s(q,f)/ideal",
                "SurfaceOutputVariable",
                dim=2,
                conc_exp=0.5,
                axis="dcsf/axes/q|dcsf/axes/omega",
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
