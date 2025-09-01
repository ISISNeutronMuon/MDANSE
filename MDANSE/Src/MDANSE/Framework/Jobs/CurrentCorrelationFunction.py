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
from math import sqrt

import numpy as np
from more_itertools import always_iterable
from scipy.signal import correlate

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
    pair_labels,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import (
    differentiate,
    get_spectrum,
)
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

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {"dependencies": {"trajectory": "trajectory", "frames": "frames"}},
    )
    settings["interpolation_order"] = (
        "InterpolationOrderConfigurator",
        {
            "label": "velocities",
            "dependencies": {"trajectory": "trajectory", "frames": "frames"},
        },
    )
    settings["q_vectors"] = (
        "QVectorsConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
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
            "default": "equal",
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
        """Initialize the input parameters and analysis self variables."""
        super().initialize()

        self.numberOfSteps = self.configuration["q_vectors"]["n_shells"]

        nQShells = self.configuration["q_vectors"]["n_shells"]

        self._instrResolution = self.configuration["instrument_resolution"]

        self._nOmegas = self._instrResolution["n_romegas"]

        self._outputData.add(
            "ccf/axes/q",
            "LineOutputVariable",
            np.array(self.configuration["q_vectors"]["shells"]),
            units="1/nm",
        )

        self._outputData.add(
            "ccf/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "ccf/res/time_window",
            "LineOutputVariable",
            self._instrResolution["time_window_positive"],
            units="au",
        )

        self._outputData.add(
            "ccf/axes/omega",
            "LineOutputVariable",
            self._instrResolution["omega"],
            units="rad/ps",
        )

        self._outputData.add(
            "ccf/axes/romega",
            "LineOutputVariable",
            self._instrResolution["romega"],
            units="rad/ps",
        )

        self._outputData.add(
            "ccf/res/omega_window",
            "LineOutputVariable",
            self._instrResolution["omega_window"],
            axis="ccf/axes/omega",
            units="au",
        )

        self._nFrames = self.configuration["frames"]["n_frames"]
        self._elements = set(
            always_iterable(
                self.trajectory.selection_getter(self.trajectory.atom_names)
            )
        )
        self.labels = pair_labels(
            self.trajectory,
        )

        self._indicesPerElement = self.trajectory.get_indices()
        self.add_ideal_results = (
            self.configuration["instrument_resolution"]["kernel"].lower() != "ideal"
        )

        for pair_str, _ in self.labels:
            self._outputData.add(
                f"ccf/j(q,t)_long/{pair_str}",
                "SurfaceOutputVariable",
                (nQShells, self._nFrames),
                axis="ccf/axes/q|ccf/axes/time",
                units="au",
            )
            self._outputData.add(
                f"ccf/j(q,t)_trans/{pair_str}",
                "SurfaceOutputVariable",
                (nQShells, self._nFrames),
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
            if self.add_ideal_results:
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
            (nQShells, self._nFrames),
            axis="ccf/axes/q|ccf/axes/time",
            units="au",
        )
        self._outputData.add(
            "ccf/j(q,t)_trans/total",
            "SurfaceOutputVariable",
            (nQShells, self._nFrames),
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
        if self.add_ideal_results:
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

        self._order = self.configuration["interpolation_order"]["value"]

        self._cell_std = 0.0
        try:
            all_cells = [
                self.trajectory.unit_cell(frame)._unit_cell
                for frame in self.configuration["frames"]["value"]
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

    def run_step(self, index: int):
        """Calculate the current densities for the input q vector shell index.

        Parameters
        ----------
        index : int
            Index of the shell.

        """
        shell = self.configuration["q_vectors"]["shells"][index]

        trajectory = self.trajectory
        cell_present = True
        cell_fixed = True
        num_frames = len(self.configuration["frames"]["value"])
        # loop over the trajectory time steps
        for frame in self.configuration["frames"]["value"]:
            unit_cell = trajectory.unit_cell(frame)
            if unit_cell is None:
                cell_present = False
            elif not np.allclose(
                unit_cell._unit_cell,
                self._average_unit_cell._unit_cell,
            ):
                cell_fixed = False
        if not cell_present:
            qVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"]
            cell_fixed = False
        else:
            try:
                hkls = self.configuration["q_vectors"]["value"][shell]["hkls"]
            except KeyError:
                qVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"]
            else:
                if hkls is None:
                    qVectors = self.configuration["q_vectors"]["value"][shell][
                        "q_vectors"
                    ]
                else:
                    qVectors = IQVectors.hkl_to_qvectors(hkls, unit_cell)

        if not cell_present:
            LOG.warning(
                "You are running the CCF calculation on a trajectory without periodic boundary conditions."
            )
        if not cell_fixed:
            LOG.warning(
                f"The unit cell is VARIABLE with the standard deviation of {self._cell_std}. This analysis should not be used with NPT runs! PLEASE CHECK YOUR RESULTS CAREFULLY."
            )
        qVectors2 = np.sum(qVectors**2, axis=0)

        zero = qVectors2 == 0
        non_zero = qVectors2 != 0
        if all(zero):
            LOG.warning(
                "All q-vectors for this shell have a magnitude "
                "of zero, longitudinal and transverse currents "
                "are not well-defined. The current correlation "
                "for this shell will be set to zero.",
            )
            # if they are all zero we can skip this shell, the
            # results for the longitudinal and transverse current
            # correlation for this shell will be zero
            return index, None
        if any(zero):
            LOG.warning(
                "q-vectors with a magnitude of zero were used, "
                "longitudinal and transverse currents are "
                "not well-defined. Skipping these q-vectors.",
            )

        qVectors = qVectors[:, non_zero]
        qVectors2 = qVectors2[non_zero]
        nQVectors = qVectors.shape[1]
        if not cell_fixed:
            hkls = self.configuration["q_vectors"]["value"][shell]["hkls"][:, non_zero]
            qVectors = np.empty((3, nQVectors, num_frames))
            for nf, frame in enumerate(self.configuration["frames"]["value"]):
                unit_cell = trajectory.unit_cell(frame)
                qVectors[:, :, nf] = IQVectors.hkl_to_qvectors(hkls, unit_cell)
            qVectors2 = np.sum(qVectors**2, axis=0)

        rho_l = {}
        rho_t = {}
        for element in self._elements:
            rho_l[element] = np.zeros(
                (self.configuration["frames"]["number"], 3, nQVectors),
                dtype=np.complex64,
            )
            rho_t[element] = np.zeros(
                (self.configuration["frames"]["number"], 3, nQVectors),
                dtype=np.complex64,
            )

        for element, idxs in list(self._indicesPerElement.items()):
            for idx in idxs:
                coords = trajectory.read_atomic_trajectory(
                    idx,
                    first=self.configuration["frames"]["first"],
                    last=self.configuration["frames"]["last"] + 1,
                    step=self.configuration["frames"]["step"],
                )

                if self.configuration["interpolation_order"]["value"] == 0:
                    veloc = trajectory.read_configuration_trajectory(
                        idx,
                        first=self.configuration["frames"]["first"],
                        last=self.configuration["frames"]["last"] + 1,
                        step=self.configuration["frames"]["step"],
                        variable="velocities",
                    )
                else:
                    veloc = np.zeros_like(coords)
                    for axis in range(3):
                        veloc[:, axis] = differentiate(
                            coords[:, axis],
                            order=self.configuration["interpolation_order"]["value"],
                            dt=self.configuration["frames"]["time_step"],
                        )

                if qVectors.ndim > 2:
                    temp_dotprod = np.einsum("ij,jki->ik", coords, qVectors)
                    curr = np.einsum(
                        "ik,ij->ikj",
                        veloc,
                        np.exp(1j * temp_dotprod),
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
                        "ik,ij->ikj",
                        veloc,
                        np.exp(1j * np.dot(coords, qVectors)),
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

        return index, (rho_l, rho_t)

    def combine(self, index: int, x: tuple[np.ndarray, np.ndarray] | None):
        """Calculate the correlation functions of the current densities.

        Parameters
        ----------
        index : int
            The index of the q vector shell that we are calculating.
        x : tuple[np.ndarray, np.ndarray]
            A tuple of numpy arrays of the longitudinal and transverse
            currents.

        """
        if x is None:
            for pair_str, _ in self.labels:
                self._outputData[f"ccf/j(q,t)_long/{pair_str}"][index, :] = np.zeros(
                    self._nFrames,
                )
                self._outputData[f"ccf/j(q,t)_trans/{pair_str}"][index, :] = np.zeros(
                    self._nFrames,
                )
            return

        rho_l, rho_t = x
        n_configs = self.configuration["frames"]["n_configs"]
        for pair_str, (label_i, label_j) in self.labels:
            corr_l = correlate(
                rho_l[label_i], rho_l[label_j][:n_configs], mode="valid"
            )[
                :,
                0,
                0,
            ] / (3 * n_configs * rho_l[label_i].shape[2])
            self._outputData[f"ccf/j(q,t)_long/{pair_str}"][index, :] += corr_l.real
            corr_t = correlate(
                rho_t[label_i], rho_t[label_j][:n_configs], mode="valid"
            )[
                :,
                0,
                0,
            ] / (3 * n_configs * rho_t[label_i].shape[2])
            self._outputData[f"ccf/j(q,t)_trans/{pair_str}"][index, :] += corr_t.real

    def finalize(self):
        """Normalize, Fourier transform and write the results out."""
        self.configuration["q_vectors"]["generator"].write_vectors_to_file(
            self._outputData,
        )

        nAtomsPerElement = self.trajectory.get_natoms()
        for pair_str, (label_i, label_j) in self.labels:
            ni = nAtomsPerElement[label_i]
            nj = nAtomsPerElement[label_j]
            self._outputData[f"ccf/j(q,t)_long/{pair_str}"][:] /= sqrt(ni * nj)
            self._outputData[f"ccf/j(q,t)_trans/{pair_str}"][:] /= sqrt(ni * nj)
            self._outputData[f"ccf/J(q,f)_long/{pair_str}"][:] = get_spectrum(
                self._outputData[f"ccf/j(q,t)_long/{pair_str}"],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
                fft="rfft",
            )
            self._outputData[f"ccf/J(q,f)_trans/{pair_str}"][:] = get_spectrum(
                self._outputData[f"ccf/j(q,t)_trans/{pair_str}"],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
                fft="rfft",
            )
            if self.add_ideal_results:
                self._outputData[f"ccf/J(q,f)_long/ideal/{pair_str}"][:] = get_spectrum(
                    self._outputData[f"ccf/j(q,t)_long/{pair_str}"],
                    None,
                    self.configuration["instrument_resolution"]["time_step"],
                    axis=1,
                    fft="rfft",
                )
                self._outputData[f"ccf/J(q,f)_trans/ideal/{pair_str}"][:] = (
                    get_spectrum(
                        self._outputData[f"ccf/j(q,t)_trans/{pair_str}"],
                        None,
                        self.configuration["instrument_resolution"]["time_step"],
                        axis=1,
                        fft="rfft",
                    )
                )

        selected_weights, all_weights = self.trajectory.get_weights(
            prop=self.configuration["weights"]["property"]
        )
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
        if self.add_ideal_results:
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

        if self.add_ideal_results:
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
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )
        self.trajectory.close()
        super().finalize()
