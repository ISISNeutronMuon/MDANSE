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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.Mathematics.Signal import differentiate, get_spectrum


class InfraredBulk(IJob):
    """Calculates the infrared spectrum of a system bulk system.

    The infrared spectrum is calculated as the autocorrelation of the derivative
    the dipole moments.

    This analysis requires molecules to be defined in the system,
    and partial charges to be set to non-zero values.
    """

    enabled = True

    label = "Infrared Spectrum Bulk"

    category = (
        "Analysis",
        "Infrared",
    )
    PREDICTORS = ("instrument_resolution",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
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
    settings["derivative_order"] = (
        "DerivativeOrderConfigurator",
        {
            "label": "d/dt dipole numerical derivative",
            "dependencies": {"frames": "frames"},
        },
    )
    settings["distance_cutoff"] = (
        "DistCutoffConfigurator",
        {
            "label": "cutoff (nm)",
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["atom_charges"] = (
        "PartialChargeConfigurator",
        {
            "dependencies": {"trajectory": "trajectory"},
            "default": {},
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = len(self.trajectory.atom_indices)
        instrResolution = self.configuration["instrument_resolution"]

        self.add_ideal_results = (
            self.configuration["instrument_resolution"]["kernel"].lower() != "ideal"
        )
        self._outputData.add(
            "ir/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "ir/res/time_window",
            "LineOutputVariable",
            instrResolution["time_window_positive"],
            axis="ir/axes/time",
            units="au",
        )

        self._outputData.add(
            "ir/axes/omega",
            "LineOutputVariable",
            instrResolution["omega"],
            units="rad/ps",
        )
        self._outputData.add(
            "ir/axes/romega",
            "LineOutputVariable",
            instrResolution["romega"],
            units="rad/ps",
        )
        self._outputData.add(
            "ir/res/omega_window",
            "LineOutputVariable",
            instrResolution["omega_window"],
            axis="ir/axes/omega",
            units="au",
        )

        self._outputData.add(
            "ddacf/ddacf",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="ir/axes/time",
        )
        self._outputData.add(
            "ir/ir",
            "LineOutputVariable",
            (instrResolution["n_romegas"],),
            axis="ir/axes/romega",
            main_result=True,
        )
        if self.add_ideal_results:
            self._outputData.add(
                "ir/ideal",
                "LineOutputVariable",
                (instrResolution["n_romegas"],),
                axis="ir/axes/romega",
            )

    def run_step(self, index: int) -> tuple[int, np.ndarray]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            The index of the atom.

        Returns
        -------
        tuple[int, np.ndarray]
            The index of the step and the calculated d/dt dipole
            auto-correlation function for a molecule.
        """
        n_configs = self.configuration["frames"]["n_configs"]
        first_frame = self.configuration["frames"]["first"]
        step_frame = self.configuration["frames"]["step"]
        last_frame = self.configuration["frames"]["last"]
        number = self.configuration["frames"]["number"]
        n_atms = self.trajectory.get_total_natoms()

        cutoff = np.zeros(n_atms, dtype=bool)
        ddipole_i = np.zeros((number, 3))
        for i, frame_index in enumerate(
            range(
                first_frame,
                last_frame + 1,
                step_frame,
            )
        ):
            configuration = self.trajectory.configuration(frame_index)
            contiguous_configuration = configuration.contiguous_configuration()
            charges = self.trajectory.charges(frame_index)
            try:
                q_i = self.configuration["atom_charges"]["charges"][index]
            except KeyError:
                q_i = charges[index]
            ddipole_i[i] = q_i * (contiguous_configuration["coordinates"][index, :])

            coords = contiguous_configuration["coordinates"]
            coords_ref = coords[index]
            cell = configuration.unit_cell.direct
            inverse_cell = configuration.unit_cell.inverse
            diff_frac = (coords - coords_ref) @ inverse_cell
            diff_frac -= np.round(diff_frac)
            diff_coords = diff_frac @ cell
            r = np.sqrt(np.sum(diff_coords * diff_coords, axis=1))

            # smaller cutoffs reproduce molecular calculation
            # all atoms that have approached the reference atom across
            # the entire trajectory
            cutoff = np.logical_or(
                cutoff, r < self.configuration["distance_cutoff"]["value"]
            )

        for axis in range(3):
            ddipole_i[:, axis] = differentiate(
                ddipole_i[:, axis],
                order=self.configuration["derivative_order"]["value"],
                dt=step_frame,
            )

        ddipole_j = np.zeros((number, 3))
        for j, frame_index in enumerate(
            range(
                first_frame,
                last_frame + 1,
                step_frame,
            )
        ):
            configuration = self.trajectory.configuration(frame_index)
            try:
                charges = np.array(
                    [
                        self.configuration["atom_charges"]["charges"][i]
                        for i in range(n_atms)
                    ]
                )
            except KeyError:
                charges = np.array(self.trajectory.charges(frame_index))
            contiguous_configuration = configuration.contiguous_configuration()
            coords = contiguous_configuration["coordinates"]
            ddipole_j[j] = np.sum(charges[cutoff, np.newaxis] * coords[cutoff], axis=0)

        for axis in range(3):
            ddipole_j[:, axis] = differentiate(
                ddipole_j[:, axis],
                order=self.configuration["derivative_order"]["value"],
                dt=step_frame,
            )

        ddipole_ij = correlate(ddipole_i, ddipole_j[:n_configs], mode="valid") / (
            3 * n_configs
        )
        return index, ddipole_ij.T[0]

    def combine(self, index: int, x: np.ndarray):
        """Add the d/dt dipole correlation function to the results.

        Parameters
        ----------
        index : int
            The index of the molecule.
        x : np.ndarray
            d/dt dipole correlation function
        """
        self._outputData["ddacf/ddacf"] += x

    def finalize(self):
        """Average the d/dt dipole auto-correlation function and
        fourier transform to get the IR spectrum and save the results.
        """
        self._outputData["ddacf/ddacf"] /= self.numberOfSteps
        self._outputData["ir/ir"][:] = get_spectrum(
            self._outputData["ddacf/ddacf"],
            self.configuration["instrument_resolution"]["time_window"],
            self.configuration["instrument_resolution"]["time_step"],
            fft="rfft",
        )
        if self.add_ideal_results:
            self._outputData["ir/ideal"][:] = get_spectrum(
                self._outputData["ddacf/ddacf"],
                None,
                self.configuration["instrument_resolution"]["time_step"],
                fft="rfft",
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
