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
from MDANSE.Framework.Parameters import (
    CorrelationWindow,
    DynamicSingleChoice,
    FrameSelect,
    InstrumentResolution,
    InterpOrder,
    MDANSETrajectory,
    Molecule,
    OutputFile,
    PartialCharge,
    RunningMode,
)
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
    PREDICTORS = ("instrument_resolution",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory()
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    instrument_resolution = InstrumentResolution(
        depends={"trajectory": "trajectory", "window": "frame_window"},
    )
    derivative_order = InterpOrder(
        depends={"trajectory": "trajectory", "frames": "frames"},
        label="Order of the derivative of the dipole moment",
    )
    molecule_name = Molecule(depends={"choices": "trajectory"})
    atom_charges = PartialCharge(depends={"trajectory": "trajectory"})
    output_files = OutputFile()
    running_mode = RunningMode()

    def initialize(self):
        super().initialize()

        self.chemical_system = self.trajectory.chemical_system

        self.molecules = self.chemical_system._clusters[self.molecule_name]

        self.numberOfSteps = len(self.molecules)
        self.resolution = self.instrument_resolution.run_resolution

        self.add_ideal_results = self.resolution.add_ideal

        self._outputData.add(
            "ir/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )
        self._outputData.add(
            "ir/res/time_window",
            "LineOutputVariable",
            self.resolution.time_window_positive,
            axis="ir/axes/time",
            units="au",
        )

        self._outputData.add(
            "ir/axes/omega",
            "LineOutputVariable",
            self.resolution.omega,
            units="rad/ps",
        )
        self._outputData.add(
            "ir/axes/romega",
            "LineOutputVariable",
            self.resolution.romega,
            units="rad/ps",
        )
        self._outputData.add(
            "ir/res/omega_window",
            "LineOutputVariable",
            self.resolution.omega_window,
            axis="ir/axes/omega",
            units="au",
        )

        self._outputData.add(
            "ddacf/ddacf",
            "LineOutputVariable",
            (self.frame_window.n_frames,),
            axis="ir/axes/time",
        )
        self._outputData.add(
            "ir/ir",
            "LineOutputVariable",
            (self.resolution.n_romegas,),
            axis="ir/axes/romega",
            main_result=True,
        )
        if self.add_ideal_results:
            self._outputData.add(
                "ir/ideal",
                "LineOutputVariable",
                (self.resolution.n_romegas,),
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
        ddipole = np.zeros((len(self.frames), 3), dtype=np.float64)
        for i, frame_index in enumerate(
            range(
                self.frames.index_start,
                self.frames.index_stop + 1,
                self.frames.index_step,
            )
        ):
            configuration = self.trajectory.configuration(frame_index)
            masses = [
                self.trajectory.get_atom_property(
                    self.chemical_system.atom_list[index], "atomic_weight"
                )
                for index in molecule
            ]
            charges = self.trajectory.charges(frame_index)
            contiguous_configuration = configuration.contiguous_configuration()
            coords = contiguous_configuration.coordinates[molecule]
            com = center_of_mass(coords, masses)

            for idx in molecule:
                try:
                    q = self.atom_charges[idx]
                except KeyError:
                    q = charges[idx]
                ddipole[i] += q * (
                    contiguous_configuration["coordinates"][idx, :] - com
                )

        for axis in range(3):
            ddipole[:, axis] = differentiate(
                ddipole[:, axis],
                order=self.derivative_order,
                dt=self.frames.time_step,
            )

        n_configs = self.frame_window.n_configs
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
            self.resolution.time_window,
            self.frames.time_step,
            fft="rfft",
        )
        if self.add_ideal_results:
            self._outputData["ir/ideal"][:] = get_spectrum(
                self._outputData["ddacf/ddacf"],
                None,
                self.frames.time_step,
                fft="rfft",
            )

        self._outputData.write(
            self.output_files.path,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
