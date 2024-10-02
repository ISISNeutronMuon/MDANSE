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
import collections
import itertools

import numpy as np
from scipy.signal import correlate

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import (
    differentiate,
    get_spectrum,
)


class CurrentCorrelationFunctionError(Exception):
    pass


class CurrentCorrelationFunction(IJob):
    """Computes the current correlation function for a set of atoms. The
    transverse and longitudinal current correlation functions are
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
        "Dynamics",
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
            "dependencies": {"trajectory": "trajectory"},
            "default": 1,
        },
    )
    settings["q_vectors"] = (
        "QVectorsConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
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
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "b_coherent",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = self.configuration["q_vectors"]["n_shells"]

        nQShells = self.configuration["q_vectors"]["n_shells"]

        self._instrResolution = self.configuration["instrument_resolution"]

        self._nOmegas = self._instrResolution["n_romegas"]

        self._outputData.add(
            "q",
            "LineOutputVariable",
            np.array(self.configuration["q_vectors"]["shells"]),
            units="1/nm",
        )

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "time_window",
            "LineOutputVariable",
            self._instrResolution["time_window"],
            units="au",
        )

        self._outputData.add(
            "romega",
            "LineOutputVariable",
            self._instrResolution["romega"],
            units="rad/ps",
        )
        self._outputData.add(
            "omega_window",
            "LineOutputVariable",
            self._instrResolution["omega_window"],
            axis="romega",
            units="au",
        )

        self._nFrames = self.configuration["frames"]["n_frames"]
        self._elements = self.configuration["atom_selection"]["unique_names"]
        self._elementsPairs = sorted(
            itertools.combinations_with_replacement(self._elements, 2)
        )

        self._indexesPerElement = self.configuration["atom_selection"].get_indexes()

        for pair in self._elementsPairs:
            self._outputData.add(
                "j(q,t)_long_%s%s" % pair,
                "SurfaceOutputVariable",
                (nQShells, self._nFrames),
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                "j(q,t)_trans_%s%s" % pair,
                "SurfaceOutputVariable",
                (nQShells, self._nFrames),
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                "J(q,f)_long_%s%s" % pair,
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="q|romega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            self._outputData.add(
                "J(q,f)_trans_%s%s" % pair,
                "SurfaceOutputVariable",
                (nQShells, self._nOmegas),
                axis="q|romega",
                units="au",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "j(q,t)_long_total",
            "SurfaceOutputVariable",
            (nQShells, self._nFrames),
            axis="q|time",
            units="au",
        )
        self._outputData.add(
            "J(q,f)_long_total",
            "SurfaceOutputVariable",
            (nQShells, self._nOmegas),
            axis="q|romega",
            units="au",
            main_result=True,
        )
        self._outputData.add(
            "j(q,t)_trans_total",
            "SurfaceOutputVariable",
            (nQShells, self._nFrames),
            axis="q|time",
            units="au",
        )
        self._outputData.add(
            "J(q,f)_trans_total",
            "SurfaceOutputVariable",
            (nQShells, self._nOmegas),
            axis="q|romega",
            units="au",
            main_result=True,
        )

        self._order = self.configuration["interpolation_order"]["value"]

    def run_step(self, index: int):
        """Calculate the current densities for the input q vector
        shell index.

        Parameters
        ----------
        index : int
            Index of the shell.
        """
        shell = self.configuration["q_vectors"]["shells"][index]

        trajectory = self.configuration["trajectory"]["instance"]

        qVectors = self.configuration["q_vectors"]["value"][shell]["q_vectors"]
        qVectors2 = np.sum(qVectors**2, axis=0)
        nQVectors = qVectors.shape[1]

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

        for element, idxs in list(self._indexesPerElement.items()):
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

                curr = np.einsum(
                    "ik,ij->ikj", veloc, np.exp(1j * np.dot(coords, qVectors))
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

    def combine(self, index: int, x: tuple[np.ndarray, np.ndarray]):
        """Calculate the correlation functions of the current densities.

        Parameters
        ----------
        index : int
            The index of the q vector shell that we are calculating.
        x : tuple[np.ndarray, np.ndarray]
            A tuple of numpy arrays of the longitudinal and transverse
            currents.
        """
        rho_l, rho_t = x
        n_configs = self.configuration["frames"]["n_configs"]
        for at1, at2 in self._elementsPairs:
            corr_l = correlate(rho_l[at1], rho_l[at2][:n_configs], mode="valid")[
                :, 0, 0
            ] / (n_configs * rho_l[at1].shape[2])
            self._outputData["j(q,t)_long_%s%s" % (at1, at2)][index, :] += corr_l.real
            corr_t = correlate(rho_t[at1], rho_t[at2][:n_configs], mode="valid")[
                :, 0, 0
            ] / (n_configs * rho_t[at1].shape[2])
            self._outputData["j(q,t)_trans_%s%s" % (at1, at2)][index, :] += corr_t.real

    def finalize(self):
        """Normalize, Fourier transform and write the results out to
        the MDA files.
        """
        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for pair in self._elementsPairs:
            at1, at2 = pair
            ni = nAtomsPerElement[at1]
            nj = nAtomsPerElement[at2]
            self._outputData["j(q,t)_long_%s%s" % pair][:] /= ni * nj
            self._outputData["j(q,t)_trans_%s%s" % pair][:] /= ni * nj
            self._outputData["J(q,f)_long_%s%s" % pair][:] = get_spectrum(
                self._outputData["j(q,t)_long_%s%s" % pair],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
                fft="rfft",
            )
            self._outputData["J(q,f)_trans_%s%s" % pair][:] = get_spectrum(
                self._outputData["j(q,t)_trans_%s%s" % pair],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
                fft="rfft",
            )

        jqtLongTotal = weight(
            self.configuration["weights"].get_weights(),
            self._outputData,
            nAtomsPerElement,
            2,
            "j(q,t)_long_%s%s",
        )
        self._outputData["j(q,t)_long_total"][:] = jqtLongTotal
        jqtTransTotal = weight(
            self.configuration["weights"].get_weights(),
            self._outputData,
            nAtomsPerElement,
            2,
            "j(q,t)_trans_%s%s",
        )
        self._outputData["j(q,t)_trans_total"][:] = jqtTransTotal

        sqfLongTotal = weight(
            self.configuration["weights"].get_weights(),
            self._outputData,
            nAtomsPerElement,
            2,
            "J(q,f)_long_%s%s",
        )
        self._outputData["J(q,f)_long_total"][:] = sqfLongTotal
        sqfTransTotal = weight(
            self.configuration["weights"].get_weights(),
            self._outputData,
            nAtomsPerElement,
            2,
            "J(q,f)_trans_%s%s",
        )
        self._outputData["J(q,f)_trans_total"][:] = sqfTransTotal

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )
        self.configuration["trajectory"]["instance"].close()
        super().finalize()
