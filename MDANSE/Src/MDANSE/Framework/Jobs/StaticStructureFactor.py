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
from collections.abc import Iterator

import numpy as np
import numpy.typing as npt

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
    update_pair_results,
)
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum


class StaticStructureFactor(DistanceHistogram):
    """Computes the static structure factor for a set of atoms.

    The static structure factor is calculated as a Fourier transform of the partial pair
    distribution function (following the Faber-Ziman definition).
    """

    label = "Static Structure Factor"

    enabled = True

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["r_values"] = (
        "DistHistCutoffConfigurator",
        {
            "label": "r values (nm)",
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "dependencies": {"trajectory": "trajectory"},
        },
    )
    settings["q_values"] = (
        "RangeConfigurator",
        {"valueType": float, "includeLast": True, "mini": 0.0, "default": (0, 500, 1)},
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
        frame_index = self.configuration["frames"]["value"][0]
        trajectory = self.configuration.get("trajectory")["instance"]

        conf = trajectory.configuration(frame_index)
        try:
            cell_volume = conf.unit_cell.volume
        except Exception:
            raise ValueError(
                "Static Structure Factor cannot be computed for chemical system without a defined simulation box. "
                "You can add a box using TrajectoryEditor."
            )
        if abs(cell_volume) < 1e-11:
            raise ValueError(
                f"Non-physical unit cell volume: {cell_volume}. Static Structure Factor will not be calculated. "
                "You can add a box using TrajectoryEditor."
            )
        return super().initialize()

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        nq = self.configuration["q_values"]["number"]

        nFrames = self.configuration["frames"]["number"]

        self.averageDensity /= nFrames

        densityFactor = 4.0 * np.pi * self.configuration["r_values"]["mid_points"]

        shellSurfaces = densityFactor * self.configuration["r_values"]["mid_points"]

        shellVolumes = shellSurfaces * self.configuration["r_values"]["step"]

        self._outputData.add(
            "ssf/axes/q",
            "LineOutputVariable",
            self.configuration["q_values"]["value"],
            units="1/nm",
        )

        nAtomsPerElement = self.trajectory.get_natoms()

        for label, _ in self.labels:
            self._outputData.add(
                f"ssf/{label}",
                "LineOutputVariable",
                (nq,),
                axis="ssf/axes/q",
                units="au",
                main_result=True,
                partial_result=True,
            )
        if self.intra:
            for label, _ in self.labels_intra:
                self._outputData.add(
                    f"ssf/intra/{label}",
                    "LineOutputVariable",
                    (nq,),
                    axis="ssf/axes/q",
                    units="au",
                )
            for label, _ in self.labels:
                self._outputData.add(
                    f"ssf/inter/{label}",
                    "LineOutputVariable",
                    (nq,),
                    axis="ssf/axes/q",
                    units="au",
                )

        self._outputData.add(
            "ssf/total",
            "LineOutputVariable",
            (nq,),
            axis="ssf/axes/q",
            units="au",
            main_result=True,
        )
        if self.intra:
            self._outputData.add(
                "ssf/intra/total",
                "LineOutputVariable",
                (nq,),
                axis="ssf/axes/q",
                units="au",
            )
            self._outputData.add(
                "ssf/inter/total",
                "LineOutputVariable",
                (nq,),
                axis="ssf/axes/q",
                units="au",
            )

        q = self._outputData["ssf/axes/q"]
        r = self.configuration["r_values"]["mid_points"]

        fact1 = 4.0 * np.pi * self.averageDensity

        sincqr = np.sinc(np.outer(q, r) / np.pi)

        dr = self.configuration["r_values"]["step"]

        def calc_func(
            label_i: str, label_j: str
        ) -> Iterator[tuple[str, bool, npt.NDArray]]:
            """Calculates the SSF for a given pair of element labels.

            Parameters
            ----------
            label_i : str
                The element label.
            label_j : str
                The element label.

            Yields
            ------
            name : str
                The results name.
            inter : bool
                Whether results are for intermolecular atom pairs.
            results : npt.NDArray
                The results.
            """
            ni = nAtomsPerElement[label_i]
            nj = nAtomsPerElement[label_j]

            idi = self.selectedElements.index(label_i)
            idj = self.selectedElements.index(label_j)

            if label_i == label_j:
                nij = ni**2 / 2.0
            else:
                nij = ni * nj
                if self.intra:
                    self.h_intra[idi, idj] += self.h_intra[idj, idi]
                self.h_total[idi, idj] += self.h_total[idj, idi]

            fact = 2 * nij * nFrames * shellVolumes

            pdfTotal = self.h_total[idi, idj, :] / fact
            yield (
                "ssf",
                False,
                1.0 + fact1 * np.sum((r**2) * (pdfTotal - 1.0) * sincqr, axis=1) * dr,
            )

            if self.intra:
                pdfIntra = self.h_intra[idi, idj, :] / fact
                pdfInter = pdfTotal - pdfIntra
                yield (
                    "ssf/inter",
                    False,
                    1.0
                    + fact1 * np.sum((r**2) * (pdfInter - 1.0) * sincqr, axis=1) * dr,
                )
                yield (
                    "ssf/intra",
                    True,
                    fact1 * np.sum((r**2) * pdfIntra * sincqr, axis=1) * dr,
                )

        update_pair_results(self.trajectory, calc_func, self._outputData)

        selected_weights, all_weights = self.trajectory.get_weights(
            prop=self.configuration["weights"]["property"]
        )
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            2,
        )

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = (n_selected / n_total) ** 2

        if self.intra:
            assign_weights(
                self._outputData, weight_dict, "ssf/intra/%s", self.labels_intra
            )
            assign_weights(self._outputData, weight_dict, "ssf/inter/%s", self.labels)
            assign_weights(self._outputData, weight_dict, "ssf/%s", self.labels)
            ssfIntra = weighted_sum(self._outputData, "ssf/intra/%s", self.labels_intra)
            self._outputData["ssf/intra/total"][:] = ssfIntra / fact
            ssfInter = weighted_sum(self._outputData, "ssf/inter/%s", self.labels)
            self._outputData["ssf/inter/total"][:] = ssfInter / fact
            self._outputData["ssf/total"][:] = (ssfIntra + ssfInter) / fact
            self._outputData["ssf/intra/total"].scaling_factor = fact
            self._outputData["ssf/inter/total"].scaling_factor = fact
            self._outputData["ssf/total"].scaling_factor = fact

            for i in ("/intra", "/inter", ""):
                add_grouped_totals(
                    self.trajectory,
                    self._outputData,
                    f"ssf{i}",
                    "LineOutputVariable",
                    dim=2,
                    intra=i == "/intra",
                    axis="ssf/axes/q",
                    units="au",
                    main_result=i == "",
                    partial_result=i == "",
                )
        else:
            assign_weights(self._outputData, weight_dict, "ssf/%s", self.labels)
            self._outputData["ssf/total"][:] = (
                weighted_sum(self._outputData, "ssf/%s", self.labels) / fact
            )
            self._outputData["ssf/total"].scaling_factor = fact

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
