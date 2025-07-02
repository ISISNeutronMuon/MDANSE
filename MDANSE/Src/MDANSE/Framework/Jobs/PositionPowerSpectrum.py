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
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MLogging import LOG


class PositionPowerSpectrum(IJob):
    """Calculates the position power spectrum.

    Power spectrum (using Fast Fourier Transform) of atomic trajectories calculated
    from the Positional Autocorrelation Function (PACF). The calculation result
    is similar to the density of states, which is calculated from the velocity
    autocorrelation function. In fact, PPS and DOS may show the same features
    in systems where position and velocity are strongly correlated (i.e. solids).

    This calculation is used by TrajectoryFilter to create a preview of the spectrum,
    so that a desired range of atomic vibrational modes can be isolated.
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
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
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
                "atom_selection": "atom_selection",
                "grouping_level": "grouping_level",
            }
        },
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "atomic_weight",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
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

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        instrResolution = self.configuration["instrument_resolution"]

        self.add_ideal_results = (
            self.configuration["instrument_resolution"]["kernel"] != "ideal"
        )

        self.labels = [
            (element, (element,))
            for element in self.configuration["atom_selection"].get_natoms()
        ]

        self._outputData.add(
            "pps/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "pacf/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "pps/res/time_window",
            "LineOutputVariable",
            instrResolution["time_window_positive"],
            axis="pps/axes/time",
            units="au",
        )

        self._outputData.add(
            "pps/axes/omega",
            "LineOutputVariable",
            instrResolution["omega"],
            units="rad/ps",
        )
        self._outputData.add(
            "pps/axes/romega",
            "LineOutputVariable",
            instrResolution["romega"],
            units="rad/ps",
        )
        self._outputData.add(
            "pps/res/omega_window",
            "LineOutputVariable",
            instrResolution["omega_window"],
            axis="pps/axes/omega",
            units="au",
        )

        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                f"pacf/{element}",
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="pacf/axes/time",
                units="nm2",
            )
            self._outputData.add(
                f"pps/{element}",
                "LineOutputVariable",
                (instrResolution["n_romegas"],),
                axis="pps/axes/romega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            if self.add_ideal_results:
                self._outputData.add(
                    f"pps/ideal/{element}",
                    "LineOutputVariable",
                    (instrResolution["n_romegas"],),
                    axis="pps/axes/romega",
                    units="au",
                )

        self._outputData.add(
            "pacf/total",
            "LineOutputVariable",
            (self.configuration["frames"]["n_frames"],),
            axis="pacf/axes/time",
            units="nm2",
        )
        self._outputData.add(
            "pps/total",
            "LineOutputVariable",
            (instrResolution["n_romegas"],),
            axis="pps/axes/romega",
            units="au",
            main_result=True,
        )
        if self.add_ideal_results:
            self._outputData.add(
                "pps/ideal/total",
                "LineOutputVariable",
                (instrResolution["n_romegas"],),
                axis="pps/axes/romega",
                units="au",
            )

        self._atoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.atom_list

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
        indices = self.configuration["atom_selection"]["indices"][index]

        series = trajectory.read_com_trajectory(
            indices,
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

        self._outputData[f"pacf/{element}"] += x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData[f"pacf/{element}"][:] /= number
            self._outputData[f"pps/{element}"][:] = get_spectrum(
                self._outputData[f"pacf/{element}"],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                fft="rfft",
            )
            if self.add_ideal_results:
                self._outputData[f"pps/ideal/{element}"][:] = get_spectrum(
                    self._outputData[f"pacf/{element}"],
                    None,
                    self.configuration["instrument_resolution"]["time_step"],
                    fft="rfft",
                )

        selected_weights, all_weights = self.configuration["weights"].get_weights()
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.configuration["atom_selection"].get_all_natoms(),
            1,
        )
        assign_weights(self._outputData, weight_dict, "pacf/%s", self.labels)
        assign_weights(self._outputData, weight_dict, "pps/%s", self.labels)
        if self.add_ideal_results:
            assign_weights(self._outputData, weight_dict, "pps/ideal/%s", self.labels)

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.configuration["atom_selection"].get_all_natoms().values())
        fact = n_selected / n_total

        self._outputData["pacf/total"][:] = (
            weighted_sum(
                self._outputData,
                "pacf/%s",
                self.labels,
            )
            / fact
        )
        self._outputData["pacf/total"].scaling_factor = fact
        self._outputData["pps/total"][:] = (
            weighted_sum(
                self._outputData,
                "pps/%s",
                self.labels,
            )
            / fact
        )
        self._outputData["pps/total"].scaling_factor = fact

        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "pacf",
            "LineOutputVariable",
            axis="pacf/axes/time",
            units="nm2",
        )
        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "pps",
            "LineOutputVariable",
            axis="pps/axes/romega",
            units="au",
            main_result=True,
            partial_result=True,
        )
        if self.add_ideal_results:
            self._outputData["pps/ideal/total"][:] = (
                weighted_sum(
                    self._outputData,
                    "pps/ideal/%s",
                    self.labels,
                )
                / fact
            )
            self._outputData["pps/ideal/total"].scaling_factor = fact
            self.configuration["grouping_level"].add_grouped_totals(
                self._outputData,
                "pps/ideal",
                "LineOutputVariable",
                axis="pps/axes/romega",
                units="au",
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
