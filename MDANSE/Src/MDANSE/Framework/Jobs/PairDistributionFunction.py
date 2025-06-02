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

import numpy as np

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

        self._outputData.add(
            "r",
            "LineOutputVariable",
            self.configuration["r_values"]["mid_points"],
            units="nm",
        )

        if self.indices_intra is not None:
            for x, y in self._elementsPairs:
                for i in ["pdf", "rdf", "tcf"]:
                    self._outputData.add(
                        f"{i}_intra_{x}{y}",
                        "LineOutputVariable",
                        (npoints,),
                        axis="r",
                        units="au",
                    )
                    self._outputData.add(
                        f"{i}_inter_{x}{y}",
                        "LineOutputVariable",
                        (npoints,),
                        axis="r",
                        units="au",
                    )
                    self._outputData.add(
                        f"{i}_{x}{y}",
                        "LineOutputVariable",
                        (npoints,),
                        axis="r",
                        units="au",
                        main_result=i == "pdf",
                        partial_result=i == "pdf",
                    )
        else:
            for x, y in self._elementsPairs:
                for i in ["pdf", "rdf", "tcf"]:
                    self._outputData.add(
                        f"{i}_{x}{y}",
                        "LineOutputVariable",
                        (npoints,),
                        axis="r",
                        units="au",
                        main_result=i == "pdf",
                        partial_result=i == "pdf",
                    )

        for i in ["pdf", "rdf", "tcf"]:
            if self.indices_intra is not None:
                self._outputData.add(
                    f"{i}_intra_total",
                    "LineOutputVariable",
                    (npoints,),
                    axis="r",
                    units="au",
                )
                self._outputData.add(
                    f"{i}_inter_total",
                    "LineOutputVariable",
                    (npoints,),
                    axis="r",
                    units="au",
                )
            self._outputData.add(
                f"{i}_total",
                "LineOutputVariable",
                (npoints,),
                axis="r",
                units="au",
                main_result=i == "pdf",
            )

        nFrames = self.configuration["frames"]["number"]

        self.averageDensity /= nFrames

        densityFactor = 4.0 * np.pi * self.configuration["r_values"]["mid_points"]

        shellSurfaces = densityFactor * self.configuration["r_values"]["mid_points"]

        shellVolumes = shellSurfaces * self.configuration["r_values"]["step"]

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()

        for pair in self._elementsPairs:
            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]

            idi = self.selectedElements.index(pair[0])
            idj = self.selectedElements.index(pair[1])

            if idi == idj:
                nij = ni**2 / 2.0
            else:
                nij = ni * nj
                if self.indices_intra is not None:
                    self.h_intra[idi, idj] += self.h_intra[idj, idi]
                self.h_total[idi, idj] += self.h_total[idj, idi]

            fact = 2 * nij * nFrames * shellVolumes

            if self.indices_intra is not None:
                pdf_intra = self.h_intra[idi, idj, :] / fact
                pdf_total = self.h_total[idi, idj, :] / fact
                pdf_inter = pdf_total - pdf_intra

                for i, pdf in zip(
                    ["_intra", "_inter", ""],
                    [pdf_intra, pdf_inter, pdf_total],
                ):
                    self._outputData[f"pdf{i}_{pair[0]}{pair[1]}"][:] = pdf
                    self._outputData[f"rdf{i}_{pair[0]}{pair[1]}"][:] = (
                        shellSurfaces * self.averageDensity * pdf
                    )
                    self._outputData[f"tcf{i}_{pair[0]}{pair[1]}"][:] = (
                        densityFactor
                        * self.averageDensity
                        * (pdf if i == "intra" else pdf - 1)
                    )
            else:
                pdf = self.h_total[idi, idj, :] / fact

                self._outputData[f"pdf_{pair[0]}{pair[1]}"][:] = pdf
                self._outputData[f"rdf_{pair[0]}{pair[1]}"][:] = (
                    shellSurfaces * self.averageDensity * pdf
                )
                self._outputData[f"tcf_{pair[0]}{pair[1]}"][:] = (
                    densityFactor * self.averageDensity * (pdf - 1)
                )

        weights = self.configuration["weights"].get_weights()
        weight_dict = get_weights(weights, nAtomsPerElement, 2)
        if self.indices_intra is not None:
            for i in ["_intra", "_inter", ""]:
                assign_weights(
                    self._outputData,
                    weight_dict,
                    f"pdf{i}_%s%s",
                )
                pdf = weighted_sum(
                    self._outputData,
                    weight_dict,
                    f"pdf{i}_%s%s",
                )
                self._outputData[f"pdf{i}_total"][:] = pdf
                self._outputData[f"rdf{i}_total"][:] = (
                    shellSurfaces * self.averageDensity * pdf
                )
                self._outputData[f"tcf{i}_total"][:] = (
                    densityFactor
                    * self.averageDensity
                    * (pdf if i == "_intra" else pdf - 1)
                )
        else:
            assign_weights(
                self._outputData,
                weight_dict,
                "pdf_%s%s",
            )
            pdf = weighted_sum(
                self._outputData,
                weight_dict,
                "pdf_%s%s",
            )
            self._outputData["pdf_total"][:] = pdf
            self._outputData["rdf_total"][:] = shellSurfaces * self.averageDensity * pdf
            self._outputData["tcf_total"][:] = (
                densityFactor * self.averageDensity * (pdf - 1)
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
