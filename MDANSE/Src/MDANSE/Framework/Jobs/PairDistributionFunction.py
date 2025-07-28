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

from collections.abc import Iterator

import numpy as np
import numpy.typing as npt

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
    update_pair_results,
)
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum


class PairDistributionFunction(DistanceHistogram):
    """Calculates a histogram of interatomic distances.

    The Pair-Distribution Function (PDF) is an example of a pair correlation function,
    which describes how, on average, the atoms in a system are radially packed around
    each other. This is a particularly effective way of describing the average
    structure of disordered molecular systems such as liquids. Also in systems like
    liquids, where there is continual movement of the atoms and a single snapshot of
    the system shows only the instantaneous disorder, it is essential to determine
    the average structure.

    The PDF can be compared with experimental data from x-ray or neutron diffraction.
        It can be used in conjunction with the inter-atomic pair potential
    function to calculate the internal energy of the system, usually quite accurately.
        Finally it can even be used to derive the inter-atomic potentials of mean force.
    """

    label = "Pair Distribution Function"

    enabled = True

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    def finalize(self):
        """Perform the last steps of the analysis and write out results."""
        npoints = len(self.configuration["r_values"]["mid_points"])

        for i in ("pdf", "rdf", "tcf"):
            self._outputData.add(
                f"{i}/axes/r",
                "LineOutputVariable",
                self.configuration["r_values"]["mid_points"],
                units="nm",
            )
            for label, _ in self.labels:
                self._outputData.add(
                    f"{i}/{label}",
                    "LineOutputVariable",
                    (npoints,),
                    axis=f"{i}/axes/r",
                    units="au",
                    main_result=i == "pdf",
                    partial_result=i == "pdf",
                )
            self._outputData.add(
                f"{i}/total",
                "LineOutputVariable",
                (npoints,),
                axis=f"{i}/axes/r",
                units="au",
                main_result=i == "pdf",
            )
            if self.intra:
                for label, _ in self.labels_intra:
                    self._outputData.add(
                        f"{i}/intra/{label}",
                        "LineOutputVariable",
                        (npoints,),
                        axis=f"{i}/axes/r",
                        units="au",
                    )
                for label, _ in self.labels:
                    self._outputData.add(
                        f"{i}/inter/{label}",
                        "LineOutputVariable",
                        (npoints,),
                        axis=f"{i}/axes/r",
                        units="au",
                    )
                self._outputData.add(
                    f"{i}/intra/total",
                    "LineOutputVariable",
                    (npoints,),
                    axis=f"{i}/axes/r",
                    units="au",
                )
                self._outputData.add(
                    f"{i}/inter/total",
                    "LineOutputVariable",
                    (npoints,),
                    axis=f"{i}/axes/r",
                    units="au",
                )

        nFrames = self.configuration["frames"]["number"]

        self.averageDensity /= nFrames

        densityFactor = 4.0 * np.pi * self.configuration["r_values"]["mid_points"]

        shellSurfaces = densityFactor * self.configuration["r_values"]["mid_points"]

        shellVolumes = shellSurfaces * self.configuration["r_values"]["step"]

        nAtomsPerElement = self.trajectory.get_natoms()

        def calc_func(
            label_i: str, label_j: str
        ) -> Iterator[tuple[str, bool, npt.NDArray]]:
            """Calculates the PDF, RDF and TCF for a given pair of
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
                if self.intra:
                    self.h_intra[idi, idj] += self.h_intra[idj, idi]
                self.h_total[idi, idj] += self.h_total[idj, idi]

            fact = 2 * nij * nFrames * shellVolumes

            for i, pdf in zip(
                ("", "/intra", "/inter"),
                (
                    pdf_total := self.h_total[idi, idj, :] / fact,
                    pdf_intra := self.h_intra[idi, idj, :] / fact
                    if self.intra
                    else None,
                    pdf_total - pdf_intra if self.intra else None,
                ),
            ):
                yield f"pdf{i}", i == "/intra", pdf
                yield (
                    f"rdf{i}",
                    i == "/intra",
                    shellSurfaces * self.averageDensity * pdf,
                )
                yield (
                    f"tcf{i}",
                    i == "/intra",
                    densityFactor
                    * self.averageDensity
                    * (pdf if i == "/intra" else pdf - 1),
                )
                if self.indices_intra is None:
                    break

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
        factor = (n_selected / n_total) ** 2

        if self.intra:
            for i in ("/intra", "/inter", ""):
                if i == "/intra":
                    labels = self.labels_intra
                else:
                    labels = self.labels
                assign_weights(self._outputData, weight_dict, f"pdf{i}/%s", labels)
                pdf = weighted_sum(self._outputData, f"pdf{i}/%s", labels)
                self._outputData[f"pdf{i}/total"][:] = pdf / factor
                self._outputData[f"rdf{i}/total"][:] = (
                    shellSurfaces * self.averageDensity * pdf / factor
                )
                self._outputData[f"tcf{i}/total"][:] = (
                    densityFactor
                    * self.averageDensity
                    * (pdf / factor if i == "/intra" else (pdf - factor) / factor)
                )
                for j in ("pdf", "rdf", "tcf"):
                    self._outputData[f"{j}{i}/total"].scaling_factor = factor
                    add_grouped_totals(
                        self.trajectory,
                        self._outputData,
                        f"{j}{i}",
                        "LineOutputVariable",
                        dim=2,
                        intra=i == "/intra",
                        axis=f"{j}/axes/r",
                        units="au",
                        main_result=j == "pdf" and i == "",
                        partial_result=j == "pdf" and i == "",
                    )
        else:
            assign_weights(self._outputData, weight_dict, "pdf/%s", self.labels)
            pdf = weighted_sum(self._outputData, "pdf/%s", self.labels)
            self._outputData["pdf/total"][:] = pdf / factor
            self._outputData["rdf/total"][:] = (
                shellSurfaces * self.averageDensity * pdf / factor
            )
            self._outputData["tcf/total"][:] = (
                densityFactor * self.averageDensity * (pdf - factor) / factor
            )
            self._outputData["pdf/total"].scaling_factor = factor
            self._outputData["rdf/total"].scaling_factor = factor
            self._outputData["tcf/total"].scaling_factor = factor

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
