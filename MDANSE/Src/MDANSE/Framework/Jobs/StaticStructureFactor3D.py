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

import itertools as it
from math import sqrt

import finufft
import numpy as np

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
    pair_labels,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum


@IJob.register("StaticStructureFactor3D")
class StaticStructureFactor3D(IJob):
    label = "Static Structure Factor 3D"

    category = (
        "Analysis",
        "Scattering",
    )
    PREDICTORS = ("q_shells",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["q_shells"] = (
        "QRangeConfigurator",
        {"default": [-10, 10, 1], "valueType": float, "includeLast": True},
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
            "default": "b_coherent",
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
        super().initialize()

        # TODO add so q_x q_y q_x ranges can be changed
        self.qxs = self.configuration["q_shells"]["value"]
        self.qys = self.configuration["q_shells"]["value"]
        self.qzs = self.configuration["q_shells"]["value"]

        min_qx = -self.qxs[-1]
        min_qy = -self.qys[-1]
        min_qz = -self.qzs[-1]
        max_qx = self.qxs[-1]
        max_qy = self.qys[-1]
        max_qz = self.qzs[-1]

        unit_cell = self.trajectory.unit_cell(0)
        self.inverse = unit_cell.inverse

        self.max_hkl = np.zeros(3, dtype=int)
        for point in it.product(
            *zip([min_qx, min_qy, min_qz], [max_qx, max_qy, max_qz], strict=False)
        ):
            hkl = np.dot(unit_cell.direct, point) / (2 * np.pi)
            self.max_hkl = np.maximum(self.max_hkl, np.floor(np.abs(hkl)).astype(int))

        self.gdim = 2 * self.max_hkl + 1
        self.numberOfSteps = self.configuration["frames"]["number"]

        self.min = -2 * np.pi * np.dot(unit_cell.inverse, self.max_hkl)
        self.spacing = 2 * np.pi * np.sum(unit_cell.inverse, axis=0)

        self._outputData.add("origin", "LineOutputVariable", self.min, units="1/nm")
        self._outputData.add(
            "spacing",
            "LineOutputVariable",
            self.spacing,
            units="1/nm",
        )

        self._indicesPerElement = self.trajectory.get_indices()
        self.labels = pair_labels(self.trajectory)

        labels = ["x_position", "y_position", "z_position"]
        for naxis in range(3):
            self._outputData.add(
                labels[naxis],
                "LineOutputVariable",
                np.arange(0, self.gdim[naxis], 1) * self.spacing[naxis]
                + self.min[naxis],
                units="1/nm",
            )

        for label, _ in self.labels:
            self._outputData.add(
                f"ssf3d/{label}",
                "VolumeOutputVariable",
                tuple(self.gdim),
                axis="|".join(labels),
                main_result=True,
                partial_result=True,
            )
        self._outputData.add(
            "ssf3d/total",
            "VolumeOutputVariable",
            tuple(self.gdim),
            axis="|".join(labels),
            main_result=True,
        )

    def run_step(self, index):
        frame = self.configuration["frames"]["value"][index]
        coords = self.trajectory.configuration(frame)["coordinates"]

        rho = {}
        for element, idxs in self._indicesPerElement.items():
            pts = 2 * np.pi * coords[idxs] @ self.inverse
            rho[element] = finufft.nufft3d1(
                pts[:, 0],
                pts[:, 1],
                pts[:, 2],
                np.ones(len(pts), dtype=np.complex128),
                n_modes=(
                    2 * self.max_hkl[0] + 1,
                    2 * self.max_hkl[1] + 1,
                    2 * self.max_hkl[2] + 1,
                ),
                eps=1e-3,
            )

        return index, rho

    def combine(self, index, rho):
        for pair_str, (label_i, label_j) in self.labels:
            self._outputData[f"ssf3d/{pair_str}"] += (
                rho[label_i] * rho[label_j].conj()
            ).real / self.numberOfSteps

    def finalize(self):
        nAtomsPerElement = self.trajectory.get_natoms()
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
        assign_weights(self._outputData, weight_dict, "ssf3d/%s", self.labels)
        for pair_str, (label_i, label_j) in self.labels:
            ni = nAtomsPerElement[label_i]
            nj = nAtomsPerElement[label_j]
            self._outputData[f"ssf3d/{pair_str}"] /= sqrt(ni * nj)

        n_selected = sum(nAtomsPerElement.values())
        n_total = len(self.trajectory.atom_types)
        fact = n_selected / n_total

        self._outputData["ssf3d/total"][:] = (
            weighted_sum(self._outputData, "ssf3d/%s", self.labels) / fact
        )
        self._outputData["ssf3d/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "ssf3d",
            "VolumeOutputVariable",
            dim=2,
            conc_exp=0.5,
            axis="x_position|y_position|z_position",
        )

        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
