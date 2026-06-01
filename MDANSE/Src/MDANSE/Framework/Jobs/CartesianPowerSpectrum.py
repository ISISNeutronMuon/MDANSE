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
import copy
import itertools as it

from more_itertools import value_chain

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.VelocityCorrelationFunction import (
    CartesianCorrelationFunction,
)
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
    PartialCharge,
    Projection,
    RunningMode,
    Weights,
)
from MDANSE.Mathematics.Arithmetic import assign_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum


class CartesianPowerSpectrum(CartesianCorrelationFunction):
    category = (
        "Analysis",
        "Dynamics",
    )
    PREDICTORS = ("instrument_resolution",)

    trajectory = MDANSETrajectory(
        selection="atom_selection",
        grouping="grouping_level",
        transmutation="atom_transmutation",
    )
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    frame_window = CorrelationWindow(depends={"frames": "frames"})
    grouping_level = GroupingLevel(depends={"trajectory": "trajectory"})
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    atom_transmutation = AtomTransmutation(depends={"trajectory": "trajectory"})
    projection = Projection(label="Project coordinates")
    atom_charges = PartialCharge(
        depends={"trajectory": "trajectory"},
    )
    weights = Weights(depends={"trajectory": "trajectory"}, default="atomic_weight")
    instrument_resolution = InstrumentResolution(
        depends={"trajectory": "trajectory", "window": "frame_window"}
    )
    output_files = OutputFile()
    running_mode = RunningMode()

    PWR_NAME = ""
    PWR_UNITS = ""

    def initialize_outputdata(self):
        super().initialize_outputdata()

        self.resolution = self.instrument_resolution.run_resolution

        self._outputData.add(
            f"{self.PWR_NAME}/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )

        self._outputData.add(
            f"{self.PWR_NAME}/res/time_window",
            "LineOutputVariable",
            self.resolution.time_window_positive,
            axis=f"{self.PWR_NAME}/axes/time",
            units="au",
        )

        self._outputData.add(
            f"{self.PWR_NAME}/axes/omega",
            "LineOutputVariable",
            self.resolution.omega,
            units="rad/ps",
        )
        self._outputData.add(
            f"{self.PWR_NAME}/axes/romega",
            "LineOutputVariable",
            self.resolution.romega,
            units="rad/ps",
        )
        self._outputData.add(
            f"{self.PWR_NAME}/res/omega_window",
            "LineOutputVariable",
            self.resolution.omega_window,
            axis=f"{self.PWR_NAME}/axes/omega",
            units="au",
        )

        self._pwr_components = self._cf_components.copy()
        if self.resolution.add_ideal:
            self._pwr_components.append("ideal/isotropic")
            for i, j in it.combinations_with_replacement("xyz", 2):
                self._pwr_components.append(f"ideal/{i}{j}")

        for component in self._pwr_components:
            for result in value_chain(self.trajectory.unique_names, "total"):
                main_result = f"{self.PWR_NAME}/{component}/" == self.MAIN_RESULTS
                partial_result = main_result and result != "total"
                self._outputData.add(
                    f"{self.PWR_NAME}/{component}/{result}",
                    "LineOutputVariable",
                    (self.resolution.n_romegas,),
                    axis=f"{self.PWR_NAME}/axes/romega",
                    units="au",
                    main_result=main_result,
                    partial_result=partial_result,
                )

    def weight_and_group(self):
        super().weight_and_group()

        nAtomsPerElement = self.trajectory.get_natoms()
        fact = sum(nAtomsPerElement.values()) / len(self.trajectory.atom_types)
        time_window = self.resolution.time_window

        for component in self._pwr_components:
            for element in nAtomsPerElement:
                self._outputData[f"{self.PWR_NAME}/{component}/{element}"][:] = (
                    get_spectrum(
                        self._outputData[
                            f"{self.CF_NAME}/{component.split('/')[-1]}/{element}"
                        ],
                        None if "ideal" in component else time_window,
                        self.frames.time_step,
                        fft="rfft",
                    )
                )

            assign_weights(
                self._outputData,
                self.weight_dict,
                f"{self.PWR_NAME}/{component}/%s",
                self.labels,
            )

            self._outputData[f"{self.PWR_NAME}/{component}/total"][:] = (
                weighted_sum(
                    self._outputData, f"{self.PWR_NAME}/{component}/%s", self.labels
                )
                / fact
            )
            self._outputData[f"{self.PWR_NAME}/{component}/total"].scaling_factor = fact

            add_grouped_totals(
                self.trajectory,
                self._outputData,
                f"{self.PWR_NAME}/{component}",
                "LineOutputVariable",
                axis=f"{self.PWR_NAME}/axes/romega",
                units="au",
                main_result=f"{self.PWR_NAME}/{component}/" == self.MAIN_RESULTS,
                partial_result=f"{self.PWR_NAME}/{component}/" == self.MAIN_RESULTS,
            )
