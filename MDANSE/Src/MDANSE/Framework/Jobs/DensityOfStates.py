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
import itertools as it

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.VelocityCorrelationFunction import (
    VelocityCorrelationFunction,
)
from MDANSE.Mathematics.Arithmetic import assign_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum


class DensityOfStates(VelocityCorrelationFunction):
    """Calculate the vibrational density of states of the trajectory.

    The Density Of States describes the number of vibrations per unit frequency.
    In MDANSE the DOS calculation returns the Fourier transform (FT) of the weighted
    Velocity Correlation Function (vcf). With an atomic mass weighting scheme
    the MDANSE DOS result is proportional to the actual vibrational DOS.
    The partial DOS corresponds to selected sets of atoms or molecules.
    """

    label = "Density Of States"

    category = (
        "Analysis",
        "Dynamics",
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
    settings["interpolation_order"] = (
        "InterpolationOrderConfigurator",
        {
            "label": "velocities",
            "dependencies": {"trajectory": "trajectory", "frames": "frames"},
        },
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
            "default": "atomic_weight",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    MAIN_RESULTS = "dos/isotropic/"

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        self.add_ideal_results = (
            self.configuration["instrument_resolution"]["kernel"].lower() != "ideal"
        )
        super().initialize()

    def initialize_outputdata(self):
        super().initialize_outputdata()

        instrResolution = self.configuration["instrument_resolution"]

        self._outputData.add(
            "dos/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._outputData.add(
            "dos/res/time_window",
            "LineOutputVariable",
            instrResolution["time_window_positive"],
            axis="dos/axes/time",
            units="au",
        )

        self._outputData.add(
            "dos/axes/omega",
            "LineOutputVariable",
            instrResolution["omega"],
            units="rad/ps",
        )
        self._outputData.add(
            "dos/axes/romega",
            "LineOutputVariable",
            instrResolution["romega"],
            units="rad/ps",
        )
        self._outputData.add(
            "dos/res/omega_window",
            "LineOutputVariable",
            instrResolution["omega_window"],
            axis="dos/axes/omega",
            units="au",
        )

        self._dos_components = self._vcf_components
        if self.add_ideal_results:
            self._dos_components.append("ideal/isotropic")
            for i, j in it.combinations_with_replacement(["x", "y", "z"], 2):
                self._dos_components.append(f"ideal/{i}{j}")

        for component in self._dos_components:
            for result in list(self.trajectory.unique_names) + ["total"]:
                main_result = f"dos/{component}/" == self.MAIN_RESULTS
                partial_result = main_result and result != "total"
                self._outputData.add(
                    f"dos/{component}/{result}",
                    "LineOutputVariable",
                    (instrResolution["n_romegas"],),
                    axis="dos/axes/romega",
                    units="au",
                    main_result=main_result,
                    partial_result=partial_result,
                )

    def weight_and_group(self):
        super().weight_and_group()

        nAtomsPerElement = self.trajectory.get_natoms()
        fact = sum(nAtomsPerElement.values()) / len(self.trajectory.atom_types)
        time_window = self.configuration["instrument_resolution"]["time_window"]

        for component in self._dos_components:
            for element, number in nAtomsPerElement.items():
                self._outputData[f"dos/{component}/{element}"][:] = get_spectrum(
                    self._outputData[f"vcf/{component}/{element}"],
                    None if "ideal" in component else time_window,
                    self.configuration["instrument_resolution"]["time_step"],
                    fft="rfft",
                )

            assign_weights(
                self._outputData, self.weight_dict, f"dos/{component}/%s", self.labels
            )

            self._outputData[f"dos/{component}/total"][:] = (
                weighted_sum(self._outputData, f"dos/{component}/%s", self.labels)
                / fact
            )
            self._outputData[f"dos/{component}/total"].scaling_factor = fact

            add_grouped_totals(
                self.trajectory,
                self._outputData,
                f"dos/{component}",
                "LineOutputVariable",
                axis="dos/axes/romega",
                units="au",
                main_result=f"dos/{component}/" == self.MAIN_RESULTS,
                partial_result=f"dos/{component}/" == self.MAIN_RESULTS,
            )
