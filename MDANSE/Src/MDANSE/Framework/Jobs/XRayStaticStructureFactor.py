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
import collections
from collections.abc import Iterator

import numpy as np
import numpy.typing as npt

from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum


def atomic_scattering_factor(element, qvalues, trajectory):
    a = np.empty((4,), dtype=np.float64)
    a[0] = trajectory.get_atom_property(element, "xray_asf_a1")
    a[1] = trajectory.get_atom_property(element, "xray_asf_a2")
    a[2] = trajectory.get_atom_property(element, "xray_asf_a3")
    a[3] = trajectory.get_atom_property(element, "xray_asf_a4")

    b = np.empty((4,), dtype=np.float64)
    b[0] = trajectory.get_atom_property(element, "xray_asf_b1")
    b[1] = trajectory.get_atom_property(element, "xray_asf_b2")
    b[2] = trajectory.get_atom_property(element, "xray_asf_b3")
    b[3] = trajectory.get_atom_property(element, "xray_asf_b4")

    c = trajectory.get_atom_property(element, "xray_asf_c")

    return c + np.sum(
        a[:, np.newaxis]
        * np.exp(-b[:, np.newaxis] * (qvalues[np.newaxis, :] / (4.0 * np.pi)) ** 2),
        axis=0,
    )


class XRayStaticStructureFactor(DistanceHistogram):
    """
    Computes the X-ray static structure from the pair distribution function for a set of atoms,
        taking into account the atomic form factor for X-rays.
    """

    label = "XRay Static Structure Factor"

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
    settings["q_values"] = (
        "RangeConfigurator",
        {"valueType": float, "includeLast": True, "mini": 0.0, "default": (0, 500, 1)},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
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
                "atom_selection": "atom_selection",
                "grouping_level": "grouping_level",
            }
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

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
            "q",
            "LineOutputVariable",
            self.configuration["q_values"]["value"],
            units="1/nm",
        )

        q = self._outputData["q"]
        r = self.configuration["r_values"]["mid_points"]

        fact1 = 4.0 * np.pi * self.averageDensity

        sincqr = np.sinc(np.outer(q, r) / np.pi)

        dr = self.configuration["r_values"]["step"]

        for label, _ in self.labels:
            self._outputData.add(
                f"xssf_{label}",
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
                main_result=True,
                partial_result=True,
            )
        self._outputData.add(
            "xssf_total",
            "LineOutputVariable",
            (nq,),
            axis="q",
            units="au",
            main_result=True,
        )
        if self.intra:
            for label, _ in self.labels_intra:
                self._outputData.add(
                    f"xssf_intra_{label}",
                    "LineOutputVariable",
                    (nq,),
                    axis="q",
                    units="au",
                )
            for label, _ in self.labels:
                self._outputData.add(
                    f"xssf_inter_{label}",
                    "LineOutputVariable",
                    (nq,),
                    axis="q",
                    units="au",
                )
            self._outputData.add(
                "xssf_intra_total",
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
            )
            self._outputData.add(
                "xssf_inter_total",
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
            )

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()

        def calc_func(
            label_i: str, label_j: str
        ) -> Iterator[tuple[str, bool, npt.NDArray]]:
            """Calculates the xray static structure factor for a given
            pair of element labels.

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
                if self.indices_intra is not None:
                    self.h_intra[idi, idj] += self.h_intra[idj, idi]
                self.h_total[idi, idj] += self.h_total[idj, idi]

            fact = 2 * nij * nFrames * shellVolumes

            pdfTotal = self.h_total[idi, idj, :] / fact
            yield (
                "xssf",
                False,
                1.0 + fact1 * np.sum((r**2) * (pdfTotal - 1.0) * sincqr, axis=1) * dr,
            )

            if self.intra:
                pdfIntra = self.h_intra[idi, idj, :] / fact
                pdfInter = pdfTotal - pdfIntra
                yield (
                    "xssf_inter",
                    False,
                    1.0
                    + fact1 * np.sum((r**2) * (pdfInter - 1.0) * sincqr, axis=1) * dr,
                )
                yield (
                    "xssf_intra",
                    True,
                    fact1 * np.sum((r**2) * pdfIntra * sincqr, axis=1) * dr,
                )

        self.configuration["grouping_level"].update_pair_results(
            calc_func, self._outputData
        )

        asf = {
            name: atomic_scattering_factor(
                ele[0],
                self._outputData["q"],
                self.configuration["trajectory"]["instance"],
            )
            for name, ele in zip(
                self.configuration["atom_selection"]["names"],
                self.configuration["atom_selection"]["elements"],
            )
        }
        all_asf = {
            name: atomic_scattering_factor(
                ele[0],
                self._outputData["q"],
                self.configuration["trajectory"]["instance"],
            )
            for name, ele in zip(
                self.configuration["atom_selection"]["all_names"],
                self.configuration["atom_selection"]["all_elements"],
            )
        }
        weight_dict = get_weights(
            asf,
            all_asf,
            nAtomsPerElement,
            self.configuration["atom_selection"].get_all_natoms(),
            2,
        )

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.configuration["atom_selection"].get_all_natoms().values())
        fact = (n_selected / n_total) ** 2

        if self.intra:
            assign_weights(
                self._outputData, weight_dict, "xssf_intra_%s", self.labels_intra
            )
            assign_weights(self._outputData, weight_dict, "xssf_inter_%s", self.labels)
            assign_weights(self._outputData, weight_dict, "xssf_%s", self.labels)

            xssfIntra = weighted_sum(
                self._outputData, "xssf_intra_%s", self.labels_intra
            )
            self._outputData["xssf_intra_total"][:] = xssfIntra / fact
            xssfInter = weighted_sum(self._outputData, "xssf_inter_%s", self.labels)
            self._outputData["xssf_inter_total"][:] = xssfInter / fact
            self._outputData["xssf_total"][:] = (xssfIntra + xssfInter) / fact
            self._outputData["xssf_intra_total"].scaling_factor = fact
            self._outputData["xssf_inter_total"].scaling_factor = fact
            self._outputData["xssf_total"].scaling_factor = fact
            for i in ["_intra", "_inter", ""]:
                self.configuration["grouping_level"].add_grouped_totals(
                    self._outputData,
                    f"xssf{i}",
                    "LineOutputVariable",
                    dim=2,
                    intra=i == "_intra",
                    axis="q",
                    units="au",
                    main_result=i == "",
                    partial_result=i == "",
                )

        else:
            assign_weights(self._outputData, weight_dict, "xssf_%s", self.labels)
            self._outputData["xssf_total"][:] = (
                weighted_sum(self._outputData, "xssf_%s", self.labels) / fact
            )
            self._outputData["xssf_total"].scaling_factor = fact

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
