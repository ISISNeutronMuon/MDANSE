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

import numpy as np

from MDANSE.Framework.AtomGrouping.grouping import pair_labels
from MDANSE.Framework.Jobs.IJob import IJob


def q_vectors_in_cube(direct, inverse, q_mins, q_maxs):
    max_hkl = np.zeros(3)
    for point in it.product(*zip(q_mins, q_maxs, strict=False)):
        hkl = np.dot(direct, point) / (2 * np.pi)
        max_hkl = np.maximum(max_hkl, np.ceil(np.abs(hkl)))

    hs = np.arange(-max_hkl[0], max_hkl[0] + 1)
    ks = np.arange(-max_hkl[1], max_hkl[1] + 1)
    ls = np.arange(-max_hkl[2], max_hkl[2] + 1)

    q_vectors = []
    for (
        h,
        k,
        l,  # noqa: E741
    ) in it.product(hs, ks, ls):
        q_vectors.append(2 * np.pi * np.dot(inverse, [h, k, l]))
    q_vectors = np.vstack(q_vectors)
    return q_vectors[np.all((q_vectors >= q_mins) & (q_vectors <= q_maxs), axis=1)].T


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
        {"valueType": float, "includeLast": True},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]

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
        dim_qx = max_qx - min_qx
        dim_qy = max_qy - min_qy
        dim_qz = max_qz - min_qz
        spacing_qx = self.qxs[1] - min_qx
        spacing_qy = self.qys[1] - min_qy
        spacing_qz = self.qzs[1] - min_qz

        self.min = np.array([min_qx, min_qy, min_qz], dtype=np.float64)
        self.max = np.array([max_qx, max_qy, max_qz], dtype=np.float64)
        self.spacing = np.array([spacing_qx, spacing_qy, spacing_qz])

        self._outputData.add("origin", "LineOutputVariable", self.min, units="nm")

        self.gdim = np.ceil(np.array([dim_qx, dim_qy, dim_qz]) / self.spacing).astype(
            int
        )
        self._outputData.add(
            "spacing",
            "LineOutputVariable",
            self.spacing,
            units="nm",
        )
        self.grid = np.zeros(self.gdim, dtype=float)

        self._indicesPerElement = self.trajectory.get_indices()
        self.labels = pair_labels(self.trajectory, all_pairs=True)

        labels = ["x_position", "y_position", "z_position"]
        for naxis in range(3):
            self._outputData.add(
                labels[naxis],
                "LineOutputVariable",
                np.arange(0, self.gdim[naxis], 1) * self.spacing[naxis]
                + self.min[naxis],
                units="nm",
            )

        # TODO static structure factor between different element types
        self._outputData.add(
            "static_structure_factor_3d",
            "VolumeOutputVariable",
            tuple(self.gdim),
            axis="|".join(labels),
            main_result=True,
        )

    def run_step(self, index):
        traj = self.trajectory

        frame = self.configuration["frames"]["value"][index]
        coords = traj.configuration(frame)["coordinates"]

        unit_cell = self.trajectory.unit_cell(frame)
        q_vectors = q_vectors_in_cube(
            unit_cell.direct, unit_cell.inverse, self.min, self.max
        )
        q_idxs = np.floor((q_vectors.T - self.min) / self.spacing).astype(int)

        rho = {}
        for element, idxs in self._indicesPerElement.items():
            selectedCoordinates = np.take(coords, idxs, axis=0)
            rho[element] = np.sum(
                np.exp(1j * np.dot(selectedCoordinates, q_vectors)), axis=0
            )

        grid = np.zeros(self.gdim)
        for _, (label_i, label_j) in self.labels:
            np.add.at(grid, tuple(q_idxs.T), np.abs(rho[label_i] * rho[label_j]))
        return index, grid

    def combine(self, index, x):
        np.add(self.grid, x, self.grid)

    def finalize(self):
        self._outputData["static_structure_factor_3d"][:] = self.grid

        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
