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
    settings["q_vectors"] = (
        "QVectors3DConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
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

        self.q_vectors = self.configuration["q_vectors"]

        self.rng = np.random.default_rng(self.q_vectors["seed"] or None)

        unit_cell = self.trajectory.unit_cell(0)
        self.inverse = unit_cell.inverse

        self.max_hkl = self.q_vectors["max_hkl"]
        self.numberOfSteps = self.configuration["frames"]["number"]

        self._outputData.add(
            "origin",
            "LineOutputVariable",
            self.q_vectors["min_uvw"],
            units="a.u.",
        )
        self._outputData.add(
            "spacing",
            "LineOutputVariable",
            self.q_vectors["step_uvw"],
            units="a.u.",
        )

        u = self.q_vectors["u"]
        v = self.q_vectors["v"]
        w = self.q_vectors["w"]

        self.axes_labels = [
            f"[{u[0]}X, {u[1]}X, {u[2]}X]   X",
            f"[{v[0]}Y, {v[1]}Y, {v[2]}Y]   Y",
            f"[{w[0]}Z, {w[1]}Z, {w[2]}Z]   Z",
        ]
        for naxis, axis in enumerate(["u", "v", "w"]):
            self._outputData.add(
                self.axes_labels[naxis],
                "LineOutputVariable",
                (self.q_vectors[f"{axis}_range"]),
                units="a.u.",
            )

        self.gdim_uvw = self.q_vectors["gdim_uvw"]

        self._indicesPerElement = self.trajectory.get_indices()
        self.labels = pair_labels(self.trajectory)

        for label, _ in self.labels:
            self._outputData.add(
                f"ssf3d/{label}",
                "VolumeOutputVariable",
                tuple(self.gdim_uvw),
                axis="|".join(self.axes_labels),
                main_result=True,
                partial_result=True,
            )
        self._outputData.add(
            "ssf3d/total",
            "VolumeOutputVariable",
            tuple(self.gdim_uvw),
            axis="|".join(self.axes_labels),
            main_result=True,
        )

        n_samples = self.q_vectors["n_samples"] * np.prod(
            self.q_vectors["gdim_uvw"] + 2
        )

        # the output s_q will be a grid of dimensions gdim_uvw, first we
        # generate random samples in this grid plus an extra border
        # around it
        samples_grid = (
            self.rng.random((3, n_samples)) * (self.q_vectors["gdim_uvw"] + 1)[:, None]
        ) - 1
        samples_grid_idxs = np.rint(samples_grid).astype(int)

        # now we remove the points that rounded to the border grid points
        mask = np.all(
            (samples_grid_idxs >= 0)
            & (samples_grid_idxs <= (self.q_vectors["gdim_uvw"] - 1)[:, None]),
            axis=0,
        )
        samples_grid = samples_grid[:, mask]
        samples_grid_idxs = samples_grid_idxs[:, mask]

        # now convert from the grid indexes to hkl of the cell
        samples_uvw = (
            np.diag(self.q_vectors["step_uvw"]) @ samples_grid
        ) + self.q_vectors["min_uvw"][:, None]
        samples_hkl = self.q_vectors["transform"] @ samples_uvw
        self.sampling_idxs_hkl = np.rint(samples_hkl).astype(int)

        self.uniq_grid, self.uniq_grid_inv = np.unique(
            samples_grid_idxs, axis=1, return_inverse=True
        )
        self.norm = np.bincount(self.uniq_grid_inv, minlength=self.uniq_grid.shape[0])

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

        s_qs = {}
        for pair_str, (label_i, label_j) in self.labels:
            s_q = (rho[label_i] * rho[label_j].conj()).real[
                tuple(self.sampling_idxs_hkl + self.max_hkl[:, None])
            ] / self.numberOfSteps
            bincount = np.bincount(
                self.uniq_grid_inv, weights=s_q, minlength=self.uniq_grid.shape[0]
            )

            sq_uvw = np.zeros(self.q_vectors["gdim_uvw"])
            sq_uvw[tuple(self.uniq_grid)] = bincount / self.norm
            s_qs[pair_str] = sq_uvw

        return index, s_qs

    def combine(self, index, s_qs):
        for pair_str, _ in self.labels:
            self._outputData[f"ssf3d/{pair_str}"] += s_qs[pair_str]

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
            axis="|".join(self.axes_labels),
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
