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
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import differentiate, get_spectrum
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms
from MDANSE.MLogging import LOG


class PositionPowerSpectrum(IJob):
    """
    Power spectrum (using Fast Fourier Transform) of atomic trajectories calculated from the Positional Autocorrelation Function (PACF).
    This method provides a frequency-domain function for a filter (i.e. lowpass) to operate on, so that a desired range of atomic vibrational modes can be isolated.
    """

    label = "PositionPowerSpectrum"

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
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
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
            "default": "atomic_weight",
            "dependencies": {"atom_selection": "atom_selection"},
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

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        instrResolution = self.configuration["instrument_resolution"]

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "time_window",
            "LineOutputVariable",
            instrResolution["time_window_positive"],
            axis="time",
            units="au",
        )

        self._outputData.add(
            "omega", "LineOutputVariable", instrResolution["omega"], units="rad/ps"
        )
        self._outputData.add(
            "romega", "LineOutputVariable", instrResolution["romega"], units="rad/ps"
        )
        self._outputData.add(
            "omega_window",
            "LineOutputVariable",
            instrResolution["omega_window"],
            axis="omega",
            units="au",
        )

        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                "pacf_%s" % element,
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="time",
                units="nm2",
            )
            self._outputData.add(
                "pps_%s" % element,
                "LineOutputVariable",
                (instrResolution["n_romegas"],),
                axis="romega",
                units="au",
                main_result=True,
                partial_result=True,
            )
        self._outputData.add(
            "pacf_total",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="time",
            units="nm2",
        )
        self._outputData.add(
            "pps_total",
            "LineOutputVariable",
            (instrResolution["n_romegas"],),
            axis="romega",
            units="au",
            main_result=True,
        )

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. atomicES (np.array): The calculated energy spectrum for atom of index=index
            #. atomicPACF (np.array): The calculated position auto-correlation function for atom of index=index
        """
        LOG.debug(f"Running step: {index}")
        trajectory = self.configuration["trajectory"]["instance"]

        # get atom index
        indexes = self.configuration["atom_selection"]["indexes"][index]
        atoms = [self._atoms[idx] for idx in indexes]

        series = trajectory.read_com_trajectory(
            atoms,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        series = series - np.average(series, axis=0)

        series = self.configuration["projection"]["projector"](series)

        n_configs = self.configuration["frames"]["n_configs"]
        atomicPACF = correlate(series, series[:n_configs], mode="valid") / (
            3 * n_configs
        )
        return index, atomicPACF.T[0]

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        # The symbol of the atom.
        element = self.configuration["atom_selection"]["names"][index]

        self._outputData["pacf_%s" % element] += x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData["pacf_%s" % element][:] /= number
            self._outputData["pps_%s" % element][:] = get_spectrum(
                self._outputData["pacf_%s" % element],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                fft="rfft",
            )

        weights = self.configuration["weights"].get_weights()
        self._outputData["pacf_total"][:] = weight(
            weights,
            self._outputData,
            nAtomsPerElement,
            1,
            "pacf_%s",
            update_partials=True,
        )
        self._outputData["pps_total"][:] = weight(
            weights,
            self._outputData,
            nAtomsPerElement,
            1,
            "pps_%s",
            update_partials=True,
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
