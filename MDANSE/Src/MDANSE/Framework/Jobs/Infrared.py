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

import numpy as np
from scipy.signal import correlate

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.Mathematics.Signal import differentiate, get_spectrum


class Infrared(IJob):
    """Calculates the infrared spectrum of a system of molecules.

    The infrared spectrum is calculated as the autocorrelation of the derivative
    the molecular dipole moments.

    This analysis requires molecules to be defined in the system,
    and partial charges to be set to non-zero values.
    """

    enabled = True

    label = "Infrared Spectrum"

    category = (
        "Analysis",
        "Infrared",
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
    settings["derivative_order"] = (
        "DerivativeOrderConfigurator",
        {
            "label": "d/dt dipole numerical derivative",
            "dependencies": {"frames": "frames"},
        },
    )
    settings["molecule_name"] = (
        "MoleculeSelectionConfigurator",
        {
            "label": "molecule name",
            "default": "",
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

        self.chemical_system = self.configuration["trajectory"][
            "instance"
        ].chemical_system

        self.molecules = self.chemical_system._clusters[
            self.configuration["molecule_name"]["value"]
        ]

        self.numberOfSteps = len(self.molecules)
        instrResolution = self.configuration["instrument_resolution"]

        self.add_ideal_results = (
            self.configuration["instrument_resolution"]["kernel"] != "ideal"
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
            The index of the molecule.

        Returns
        -------
        tuple[int, np.ndarray]
            The index of the step and the calculated d/dt dipole
            auto-correlation function for a molecule.
        """
        molecule = self.molecules[index]
        ddipole = np.zeros(
            (self.configuration["frames"]["number"], 3), dtype=np.float64
        )
        for i, frame_index in enumerate(
            range(
                self.configuration["frames"]["first"],
                self.configuration["frames"]["last"] + 1,
                self.configuration["frames"]["step"],
            )
        ):
            configuration = self.configuration["trajectory"]["instance"].configuration(
                frame_index
            )
            masses = [
                self.configuration["trajectory"]["instance"].get_atom_property(
                    self.chemical_system.atom_list[index], "atomic_weight"
                )
                for index in molecule
            ]
            charges = self.configuration["trajectory"]["instance"].charges(frame_index)
            contiguous_configuration = configuration.contiguous_configuration()
            coords = contiguous_configuration.coordinates[molecule]
            com = center_of_mass(coords, masses)

            for idx in molecule:
                try:
                    q = self.configuration["atom_charges"]["charges"][idx]
                except KeyError:
                    q = charges[idx]
                ddipole[i] += q * (
                    contiguous_configuration["coordinates"][idx, :] - com
                )

        for axis in range(3):
            ddipole[:, axis] = differentiate(
                ddipole[:, axis],
                order=self.configuration["derivative_order"]["value"],
                dt=self.configuration["frames"]["time_step"],
            )

        n_configs = self.configuration["frames"]["n_configs"]
        mol_ddacf = correlate(ddipole, ddipole[:n_configs], mode="valid") / (
            3 * n_configs
        )
        return index, mol_ddacf.T[0]

    def combine(self, index: int, x: np.ndarray):
        """Add the d/dt dipole auto-correlation function of molecule
        to the results.

        Parameters
        ----------
        index : int
            The index of the molecule.
        x : np.ndarray
            d/dt dipole auto-correlation function for a molecule
        """
        self._outputData["ddacf/ddacf"] += x

    def finalize(self):
        """Average the d/dt dipole auto-correlation function over the
        number of molecules in the trajectory, fourier transform to
        get the IR spectrum and save the results.
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

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
