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

import abc
import collections
import itertools as it
from typing import TYPE_CHECKING

from more_itertools import value_chain
from scipy.signal import correlate

from MDANSE.Framework.AtomGrouping.grouping import add_grouped_totals
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    AtomSelection,
    AtomTransmutation,
    CorrelationWindow,
    FrameSelect,
    GroupingLevel,
    MDANSETrajectory,
    OutputFile,
    PartialCharge,
    Projection,
    RunningMode,
    Weights,
)
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt


class CartesianCorrelationFunction(IJob):
    enabled = False

    category = (
        "Analysis",
        "Dynamics",
    )
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    CF_NAME = ""
    CF_UNITS = ""
    MAIN_RESULTS = ""

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = len(self.trajectory.atom_indices)

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        selected_weights, all_weights = self.trajectory.get_weights(prop=self.weights)

        if self.weights in {"b_coherent", "b_incoherent"}:
            for weights in selected_weights, all_weights:
                for key, value in weights.items():
                    weights[key] = abs(value) ** 2

        self.weight_dict = get_weights(
            selected_weights,
            all_weights,
            self.trajectory.get_natoms(),
            self.trajectory.get_all_natoms(),
            1,
        )

        self.initialize_outputdata()

    def initialize_outputdata(self):
        self._outputData.add(
            f"{self.CF_NAME}/axes/time",
            "LineOutputVariable",
            self.frame_window.duration,
            units="ps",
        )

        self._cf_components = [
            "isotropic",
            *map("".join, it.combinations_with_replacement("xyz", 2)),
        ]

        for component in self._cf_components:
            for result in value_chain(self.trajectory.unique_names, "total"):
                main_result = f"{self.CF_NAME}/{component}/" == self.MAIN_RESULTS
                partial_result = main_result and result != "total"
                self._outputData.add(
                    f"{self.CF_NAME}/{component}/{result}",
                    "LineOutputVariable",
                    (self.frame_window.n_frames,),
                    axis=f"{self.CF_NAME}/axes/time",
                    units=self.CF_UNITS,
                    main_result=main_result,
                    partial_result=partial_result,
                )

    @abc.abstractmethod
    def get_series(self, index):
        pass

    def run_step(self, index):
        series = self.get_series(index)

        u_x = series[:, 0]
        u_y = series[:, 1]
        u_z = series[:, 2]

        n_configs = self.frame_window.n_configs
        cfs = [
            correlate(u_i, u_j[:n_configs], mode="valid").T / n_configs
            for u_i, u_j in it.combinations_with_replacement([u_x, u_y, u_z], 2)
        ]
        return index, cfs

    def combine(self, index: int, cfs: list[npt.NDArray[np.floating]]):
        """
        Combines returned results of run_step.

        Parameters
        ----------
        index : int
            The index of the step.
        cfs : Any
            The returned result(s) of run_step.
        """
        # The symbol of the atom.
        element = self.trajectory.atom_names[self.trajectory.atom_indices[index]]

        isotropic = (cfs[0] + cfs[3] + cfs[5]) / 3
        self._outputData[f"{self.CF_NAME}/isotropic/{element}"] += isotropic

        for i, (j, k) in enumerate(it.combinations_with_replacement("xyz", 2)):
            self._outputData[f"{self.CF_NAME}/{j}{k}/{element}"] += cfs[i]

    def weight_and_group(self):
        nAtomsPerElement = self.trajectory.get_natoms()
        fact = sum(nAtomsPerElement.values()) / len(self.trajectory.atom_types)

        for component in self._cf_components:
            for element, number in nAtomsPerElement.items():
                self._outputData[f"{self.CF_NAME}/{component}/{element}"][:] /= number

            assign_weights(
                self._outputData,
                self.weight_dict,
                f"{self.CF_NAME}/{component}/%s",
                self.labels,
            )

            self._outputData[f"{self.CF_NAME}/{component}/total"][:] = (
                weighted_sum(
                    self._outputData, f"{self.CF_NAME}/{component}/%s", self.labels
                )
                / fact
            )
            self._outputData[f"{self.CF_NAME}/{component}/total"].scaling_factor = fact

            add_grouped_totals(
                self.trajectory,
                self._outputData,
                f"{self.CF_NAME}/{component}",
                "LineOutputVariable",
                axis=f"{self.CF_NAME}/axes/time",
                units=self.CF_UNITS,
                main_result=f"{self.CF_NAME}/{component}/" == self.MAIN_RESULTS,
                partial_result=f"{self.CF_NAME}/{component}/" == self.MAIN_RESULTS,
            )

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        self.weight_and_group()

        self._outputData.write(
            self.output_files.path,
            self.output_files.out_format,
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
