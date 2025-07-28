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
from collections.abc import Iterator

import numpy as np
import numpy.typing as npt

from MDANSE.Framework.AtomGrouping.grouping import (
    pair_labels,
    update_pair_results,
)
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram


class CoordinationNumber(DistanceHistogram):
    """Calculates the coordination number for pairs of atom types.

    The Coordination Number is computed from the pair distribution function.
    It describes the total number of neighbours, as a function of distance,
    from a central atom, or the centre of a group of atoms.

    Please not the the Coordination Number results are not symmetrical.
    That is, the number of B atoms around an A atom is not equal to the
    number of A atoms around a B atom.
    """

    label = "Coordination Number"

    enabled = True

    category = (
        "Analysis",
        "Structure",
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
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        npoints = len(self.configuration["r_values"]["mid_points"])

        self._outputData.add(
            "cn/axes/r",
            "LineOutputVariable",
            self.configuration["r_values"]["mid_points"],
            units="nm",
        )

        self.labels = pair_labels(self.trajectory, all_pairs=True)
        self.labels_intra = pair_labels(self.trajectory, intra=True, all_pairs=True)

        for label, _ in self.labels:
            self._outputData.add(
                f"cn/{label}",
                "LineOutputVariable",
                (npoints,),
                axis="cn/axes/r",
                units="au",
                main_result=True,
            )
        if self.intra:
            for label, _ in self.labels_intra:
                self._outputData.add(
                    f"cn/intra/{label}",
                    "LineOutputVariable",
                    (npoints,),
                    axis="cn/axes/r",
                    units="au",
                )
            for label, _ in self.labels:
                self._outputData.add(
                    f"cn/inter/{label}",
                    "LineOutputVariable",
                    (npoints,),
                    axis="cn/axes/r",
                    units="au",
                )

        nFrames = self.configuration["frames"]["number"]

        densityFactor = 4.0 * np.pi * self.configuration["r_values"]["mid_points"]

        shellSurfaces = densityFactor * self.configuration["r_values"]["mid_points"]

        shellVolumes = shellSurfaces * self.configuration["r_values"]["step"]

        self.averageDensity *= 4.0 * np.pi / nFrames

        r2 = self.configuration["r_values"]["mid_points"] ** 2
        dr = self.configuration["r_values"]["step"]

        for k in self._concentrations:
            self._concentrations[k] /= nFrames

        nAtomsPerElement = self.trajectory.get_natoms()

        # symmetrize the data
        for (idi, i), (idj, j) in it.combinations_with_replacement(
            enumerate(self.selectedElements), 2
        ):
            if i == j:
                continue

            if self.indices_intra is not None:
                self.h_intra[idi, idj] += self.h_intra[idj, idi]
                self.h_intra[idj, idi] = self.h_intra[idi, idj]
            self.h_total[idi, idj] += self.h_total[idj, idi]
            self.h_total[idj, idi] = self.h_total[idi, idj]

        def calc_func(
            label_i: str, label_j: str
        ) -> Iterator[tuple[str, bool, npt.NDArray]]:
            """Calculates the coordination number for a given pair of
            element labels.

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

            fact = 2 * nij * nFrames * shellVolumes

            rho_j = self.averageDensity * self._concentrations[label_j]

            self.h_total[idi, idj, :] /= fact
            cnTotal = np.add.accumulate(self.h_total[idi, idj, :] * r2) * dr
            yield "cn", False, rho_j * cnTotal

            if self.intra:
                self.h_intra[idi, idj, :] /= fact
                cnIntra = np.add.accumulate(self.h_intra[idi, idj, :] * r2) * dr
                cnInter = cnTotal - cnIntra
                yield "cn/inter", False, rho_j * cnInter
                yield "cn/intra", True, rho_j * cnIntra

        update_pair_results(
            self.trajectory, calc_func, self._outputData, all_pairs=True
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()

        super().finalize()
