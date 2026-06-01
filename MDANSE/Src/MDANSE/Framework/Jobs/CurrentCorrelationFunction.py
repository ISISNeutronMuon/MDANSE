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
import numpy.typing as npt
from more_itertools import always_iterable
from scipy.signal import correlate

from MDANSE.Framework.AtomGrouping.grouping import add_grouped_totals, pair_labels
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    CorrelationWindow,
    FrameSelect,
    GroupingLevel,
    InstrumentResolution,
    InterpOrder,
    MDANSETrajectory,
    OutputFile,
    QVectors,
    RunningMode,
    Weights,
)
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import differentiate, get_spectrum
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class CurrentCorrelationFunctionError(Exception):
    pass


class CurrentCorrelationFunction(IJob):
    """Computes the current correlation function for a set of atoms.

    The transverse and longitudinal current correlation functions are
    typically used to study the propagation of excitations in disordered
    systems. The longitudinal current is directly related to density
    fluctuations and the transverse current is linked to propagating
    'shear modes'.

    For more information, see e.g. 'J. P. Hansen and I. R. McDonald,
    Theory of Simple Liquids (3rd ed., Elsevier), chapter 7.4:
    Correlations in space and time.'
    """

    enabled = True

    label = "Current Correlation Function"
    PREDICTORS = ("instrument_resolution", "q_vectors")

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        transmutation="atom_transmutation",
        grouping="grouping_level",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    instrument_resolution = InstrumentResolution(
        depends={"trajectory": "trajectory", "window": "frame_window"},
    )
    interpolation_order = InterpOrder(
        depends={"trajectory": "trajectory", "frames": "frames"}
    )
    q_vectors = QVectors(depends={"trajectory": "trajectory"})
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    weights = Weights(default="equal", depends={"trajectory": "trajectory"})
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.generator = self.q_vectors.generator

        self.numberOfSteps = self.generator.n_shells

        nQShells = self.generator.n_shells

        self.resolution = self.instrument_resolution.run_resolution
        self._nOmegas = self.resolution.n_romegas

        self._outputData.add(
            "ccf/axes/q",
            "LineOutputVariable",
            self.generator.shells,
            units="1/nm",
        )

        self._outputData.add(
            "ccf/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )

        self._outputData.add(
            "ccf/res/time_window",
            "LineOutputVariable",
            self.resolution.time_window_positive,
            units="au",
        )

        self._outputData.add(
            "ccf/axes/omega",
            "LineOutputVariable",
            self.resolution.omega,
            units="rad/ps",
        )

        self._outputData.add(
            "ccf/axes/romega",
            "LineOutputVariable",
            self.resolution.romega,
            units="rad/ps",
        )

        self._outputData.add(
            "ccf/res/omega_window",
            "LineOutputVariable",
            self.resolution.omega_window,
            axis="ccf/axes/omega",
            units="au",
        )

        self._elements = set(
            always_iterable(
                self.trajectory.selection_getter(self.trajectory.atom_names)
            )
        )
        self.labels = pair_labels(
            self.trajectory,
        )

        self.indices_per_element = self.trajectory.get_indices()

        for pair_str, _ in self.labels:
            self._outputData.add(
                f"ccf/j(q,t)_long/{pair_str}",
                "SurfaceOutputVariable",
                (nQShells, self.frame_window.n_frames),
                axis="ccf/axes/q|ccf/axes/time",
                units="au",
            )
            self._outputData.add(
                f"ccf/j(q,t)_trans/{pair_str}",
                "SurfaceOutputVariable",
                (nQShells, self.frame_window.n_frames),
                axis="ccf/axes/q|ccf/axes/time",
                units="au",
            )
            self._outputData.add(
                f"ccf/J(q,f)_long/{pair_str}",
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="ccf/axes/q|ccf/axes/romega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            self._outputData.add(
                f"ccf/J(q,f)_trans/{pair_str}",
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="ccf/axes/q|ccf/axes/romega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            if self.resolution.add_ideal:
                self._outputData.add(
                    f"ccf/J(q,f)_long/ideal/{pair_str}",
                    "SurfaceOutputVariable",
                    (nQShells, self._nOmegas),
                    axis="ccf/axes/q|ccf/axes/romega",
                    units="au",
                )
                self._outputData.add(
                    f"ccf/J(q,f)_trans/ideal/{pair_str}",
                    "SurfaceOutputVariable",
                    (nQShells, self._nOmegas),
                    axis="ccf/axes/q|ccf/axes/romega",
                    units="au",
                )

        self._outputData.add(
            "ccf/j(q,t)_long/total",
            "SurfaceOutputVariable",
            (nQShells, self.frame_window.n_frames),
            axis="ccf/axes/q|ccf/axes/time",
            units="au",
        )
        self._outputData.add(
            "ccf/j(q,t)_trans/total",
            "SurfaceOutputVariable",
            (nQShells, self.frame_window.n_frames),
            axis="ccf/axes/q|ccf/axes/time",
            units="au",
        )
        self._outputData.add(
            "ccf/J(q,f)_long/total",
            "SurfaceOutputVariable",
            (nQShells, self._nOmegas),
            axis="ccf/axes/q|ccf/axes/romega",
            units="au",
            main_result=True,
        )
        self._outputData.add(
            "ccf/J(q,f)_trans/total",
            "SurfaceOutputVariable",
            (nQShells, self._nOmegas),
            axis="ccf/axes/q|ccf/axes/romega",
            units="au",
            main_result=True,
        )
        if self.resolution.add_ideal:
            self._outputData.add(
                "ccf/J(q,f)_long/ideal/total",
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="ccf/axes/q|ccf/axes/romega",
                units="au",
            )
            self._outputData.add(
                "ccf/J(q,f)_trans/ideal/total",
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="ccf/axes/q|ccf/axes/romega",
                units="au",
            )

        self._order = self.interpolation_order

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

    def run_step(
        self, index: int
    ) -> tuple[
        int,
        tuple[
            dict[str, npt.NDArray[np.complexfloating]],
            dict[str, npt.NDArray[np.complexfloating]],
            float,
        ]
        | None,
    ]:
        """Calculate the current densities for the input q vector shell index.

        Parameters
        ----------
        index : int
            Index of the shell.

        """
        shell = self.generator.shells[index]

        if self.generator.q_vectors.get(shell) is None:
            LOG.warning("No q vecs at %f", shell)
            return index, None

        qvec_weights = self.generator.q_vectors[shell]["weights"]
        qvec_weights_sqrt = np.sqrt(qvec_weights)

        trajectory = self.trajectory
        cell_present = True
        cell_fixed = True
        num_frames = len(self.frames)

        # loop over the trajectory time steps
        for frame in self.frames:
            unit_cell = trajectory.unit_cell(frame.ind)
            if unit_cell is None:
                cell_present = False
                cell_fixed = False
            elif not np.allclose(
                unit_cell._unit_cell,
                self._average_unit_cell._unit_cell,
            ):
                cell_fixed = False

        if (
            cell_present
            and (hkls := self.generator.q_vectors[shell].get("hkls")) is not None
        ):
            qVectors = IQVectors.hkl_to_qvectors(hkls, unit_cell)
        else:
            qVectors = self.generator.q_vectors[shell]["q_vectors"]


        if not cell_present:
            LOG.warning(
                "You are running the CCF calculation on a trajectory without periodic boundary conditions."
            )
        if not cell_fixed:
            LOG.warning(
                f"The unit cell is VARIABLE with the standard deviation of {self._cell_std}. "
                "This analysis should not be used with NPT runs! PLEASE CHECK YOUR RESULTS CAREFULLY."
            )

        qVectors2 = np.sum(qVectors**2, axis=0)

        zero = qVectors2 == 0
        non_zero = qVectors2 != 0

        if np.all(zero):
            LOG.warning(
                "All q-vectors for this shell have a magnitude "
                "of zero, longitudinal and transverse currents "
                "are not well-defined. The current correlation "
                "for this shell will be set to zero @ %f.",
                shell
            )
            # if they are all zero we can skip this shell, the
            # results for the longitudinal and transverse current
            # correlation for this shell will be zero

            return index, None

        if np.any(zero):
            LOG.warning(
                "q-vectors with a magnitude of zero were used, "
                "longitudinal and transverse currents are "
                "not well-defined. Skipping these q-vectors.",
            )

        qVectors = qVectors[:, non_zero]
        qvec_weights = qvec_weights[non_zero]
        qVectors2 = qVectors2[non_zero]
        nQVectors = qVectors.shape[1]

        if not cell_fixed:
            hkls = self.generator.q_vectors[shell]["hkls"][:, non_zero]
            qVectors = np.empty((3, nQVectors, num_frames))
            for nf, frame in enumerate(self.frames):
                unit_cell = trajectory.unit_cell(frame.ind)
                qVectors[:, :, nf] = IQVectors.hkl_to_qvectors(hkls, unit_cell)

            qVectors2 = np.sum(qVectors**2, axis=0)

        rho_l = {
            element: np.zeros(
                (len(self.frames), 3, nQVectors),
                dtype=np.complex64,
            )
            for element in self._elements
        }
        rho_t = {
            element: np.zeros(
                (len(self.frames), 3, nQVectors),
                dtype=np.complex64,
            )
            for element in self._elements
        }

        for element, idxs in self.indices_per_element.items():
            for idx in idxs:
                coords = trajectory.read_atomic_trajectory(
                    idx,
                    first=self.frames.index_start,
                    last=self.frames.index_stop + 1,
                    step=self.frames.index_step,
                )

                if not self.interpolation_order:
                    veloc = trajectory.read_configuration_trajectory(
                        idx,
                        first=self.frames.index_start,
                        last=self.frames.index_stop + 1,
                        step=self.frames.index_step,
                        variable="velocities",
                    )
                else:
                    veloc = np.zeros_like(coords)
                    for axis in range(3):
                        veloc[:, axis] = differentiate(
                            coords[:, axis],
                            order=self.interpolation_order,
                            dt=self.frames.time_step,
                        )

                if qVectors.ndim > 2:
                    temp_dotprod = np.einsum("ij,jki->ik", coords, qVectors)
                    curr = np.einsum(
                        "ik,ij,j->ikj",
                        veloc,
                        np.exp(1j * temp_dotprod),
                        qvec_weights_sqrt,
                    )
                    long = np.einsum(
                        "lji,kji,ikj->ilj",
                        qVectors,
                        qVectors / qVectors2,
                        curr,
                    )
                    trans = curr - long
                else:
                    curr = np.einsum(
                        "ik,ij,j->ikj",
                        veloc,
                        np.exp(1j * np.dot(coords, qVectors)),
                        qvec_weights_sqrt,
                    )
                    long = np.einsum(
                        "lj,kj,ikj->ilj",
                        qVectors,
                        qVectors / qVectors2,
                        curr,
                    )
                    trans = curr - long

                rho_l[element] += long
                rho_t[element] += trans

        return index, (rho_l, rho_t, np.sum(qvec_weights))

    def combine(
        self,
        index: int,
        x: tuple[
            dict[str, npt.NDArray[np.complexfloating]],
            dict[str, npt.NDArray[np.complexfloating]],
            float,
        ]
        | None,
    ):
        """Calculate the correlation functions of the current densities.

        Parameters
        ----------
        index : int
            The index of the q vector shell that we are calculating.
        x : tuple[np.ndarray, np.ndarray, float]
            A tuple of numpy arrays of the longitudinal and transverse
            currents and vector weights.

        """
        if x is None:
            for pair_str, _ in self.labels:
                self._outputData[f"ccf/j(q,t)_long/{pair_str}"][index, :] = np.nan
                self._outputData[f"ccf/j(q,t)_trans/{pair_str}"][index, :] = np.nan
            return

        rho_l, rho_t, norm = x
        n_configs = self.frame_window.n_configs
        for pair_str, (label_i, label_j) in self.labels:
            corr_l = correlate(
                rho_l[label_i], rho_l[label_j][:n_configs], mode="valid"
            )[
                :,
                0,
                0,
            ] / (3 * n_configs * norm)
            self._outputData[f"ccf/j(q,t)_long/{pair_str}"][index, :] += corr_l.real
            corr_t = correlate(
                rho_t[label_i], rho_t[label_j][:n_configs], mode="valid"
            )[
                :,
                0,
                0,
            ] / (3 * n_configs * norm)
            self._outputData[f"ccf/j(q,t)_trans/{pair_str}"][index, :] += corr_t.real

    def finalize(self):
        """Normalize, Fourier transform and write the results out."""
        self.generator.write_vectors_to_file(self._outputData)

        nAtomsPerElement = self.trajectory.get_natoms()
        for pair_str, (label_i, label_j) in self.labels:
            ni = nAtomsPerElement[label_i]
            nj = nAtomsPerElement[label_j]
            self._outputData[f"ccf/j(q,t)_long/{pair_str}"][:] /= sqrt(ni * nj)
            self._outputData[f"ccf/j(q,t)_trans/{pair_str}"][:] /= sqrt(ni * nj)
            self._outputData[f"ccf/J(q,f)_long/{pair_str}"][:] = get_spectrum(
                self._outputData[f"ccf/j(q,t)_long/{pair_str}"],
                self.resolution.time_window,
                self.frames.time_step,
                axis=1,
                fft="rfft",
            )
            self._outputData[f"ccf/J(q,f)_trans/{pair_str}"][:] = get_spectrum(
                self._outputData[f"ccf/j(q,t)_trans/{pair_str}"],
                self.resolution.time_window,
                self.frames.time_step,
                axis=1,
                fft="rfft",
            )
            if self.resolution.add_ideal:
                self._outputData[f"ccf/J(q,f)_long/ideal/{pair_str}"][:] = get_spectrum(
                    self._outputData[f"ccf/j(q,t)_long/{pair_str}"],
                    None,
                    self.frames.time_step,
                    axis=1,
                    fft="rfft",
                )
                self._outputData[f"ccf/J(q,f)_trans/ideal/{pair_str}"][:] = (
                    get_spectrum(
                        self._outputData[f"ccf/j(q,t)_trans/{pair_str}"],
                        None,
                        self.frames.time_step,
                        axis=1,
                        fft="rfft",
                    )
                )

        selected_weights, all_weights = self.trajectory.get_weights(prop=self.weights)
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            2,
            conc_exp=0.5,
        )
        assign_weights(self._outputData, weight_dict, "ccf/j(q,t)_long/%s", self.labels)
        assign_weights(
            self._outputData, weight_dict, "ccf/j(q,t)_trans/%s", self.labels
        )
        assign_weights(self._outputData, weight_dict, "ccf/J(q,f)_long/%s", self.labels)
        assign_weights(
            self._outputData, weight_dict, "ccf/J(q,f)_trans/%s", self.labels
        )
        if self.resolution.add_ideal:
            assign_weights(
                self._outputData,
                weight_dict,
                "ccf/J(q,f)_long/ideal/%s",
                self.labels,
            )
            assign_weights(
                self._outputData,
                weight_dict,
                "ccf/J(q,f)_trans/ideal/%s",
                self.labels,
            )

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = n_selected / n_total

        jqtLongTotal = weighted_sum(self._outputData, "ccf/j(q,t)_long/%s", self.labels)
        self._outputData["ccf/j(q,t)_long/total"][:] = jqtLongTotal
        jqtTransTotal = weighted_sum(
            self._outputData, "ccf/j(q,t)_trans/%s", self.labels
        )
        self._outputData["ccf/j(q,t)_trans/total"][:] = jqtTransTotal
        self._outputData["ccf/j(q,t)_long/total"].scaling_factor = fact
        self._outputData["ccf/j(q,t)_trans/total"].scaling_factor = fact
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ccf/j(q,t)_long",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="ccf/axes/q|ccf/axes/time",
            units="au",
        )
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ccf/j(q,t)_trans",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="ccf/axes/q|ccf/axes/time",
            units="au",
        )

        sqfLongTotal = weighted_sum(self._outputData, "ccf/J(q,f)_long/%s", self.labels)
        self._outputData["ccf/J(q,f)_long/total"][:] = sqfLongTotal
        sqfTransTotal = weighted_sum(
            self._outputData, "ccf/J(q,f)_trans/%s", self.labels
        )
        self._outputData["ccf/J(q,f)_trans/total"][:] = sqfTransTotal
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ccf/J(q,f)_long",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="ccf/axes/q|ccf/axes/romega",
            units="au",
            main_result=True,
            partial_result=True,
        )
        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ccf/J(q,f)_trans",
            "SurfaceOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="ccf/axes/q|ccf/axes/romega",
            units="au",
            main_result=True,
            partial_result=True,
        )

        if self.resolution.add_ideal:
            sqfLongTotal = weighted_sum(
                self._outputData, "ccf/J(q,f)_long/ideal/%s", self.labels
            )
            self._outputData["ccf/J(q,f)_long/ideal/total"][:] = sqfLongTotal / fact
            self._outputData["ccf/J(q,f)_long/ideal/total"].scaling_factor = fact
            sqfTransTotal = weighted_sum(
                self._outputData, "J(q,f)_trans/ideal/%s", self.labels
            )
            self._outputData["ccf/J(q,f)_trans/ideal/total"][:] = sqfTransTotal / fact
            self._outputData["ccf/J(q,f)_trans/ideal/total"].scaling_factor = fact
            add_grouped_totals(
                self.trajectory,
                self._outputData,
                "ccf/J(q,f)_long/ideal",
                "SurfaceOutputVariable",
                dim=2,
                conc_exp=0.5,
                axis="ccf/axes/q|ccf/axes/romega",
                units="au",
            )
            add_grouped_totals(
                self.trajectory,
                self._outputData,
                "ccf/J(q,f)_trans/ideal",
                "SurfaceOutputVariable",
                dim=2,
                conc_exp=0.5,
                axis="ccf/axes/q|ccf/axes/romega",
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
