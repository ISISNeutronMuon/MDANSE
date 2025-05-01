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

import numpy as np

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
            }
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
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

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for pair in self._elementsPairs:
            pair_str = "".join(map(str, pair))
            self._outputData.add(
                f"xssf_intra_{pair_str}",
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
            )
            self._outputData.add(
                f"xssf_inter_{pair_str}",
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
            )
            self._outputData.add(
                f"xssf_total_{pair_str}",
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
                main_result=True,
                partial_result=True,
            )

            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]

            idi = self.selectedElements.index(pair[0])
            idj = self.selectedElements.index(pair[1])

            if pair[0] == pair[1]:
                nij = ni**2 / 2.0
            else:
                nij = ni * nj
                self.hIntra[idi, idj] += self.hIntra[idj, idi]
                self.hInter[idi, idj] += self.hInter[idj, idi]

            fact = 2 * nij * nFrames * shellVolumes

            pdfIntra = self.hIntra[idi, idj, :] / fact
            pdfInter = self.hInter[idi, idj, :] / fact

            self._outputData[f"xssf_intra_{pair_str}"][:] = (
                fact1 * np.sum((r**2) * pdfIntra * sincqr, axis=1) * dr
            )
            self._outputData[f"xssf_inter_{pair_str}"][:] = (
                1.0 + fact1 * np.sum((r**2) * (pdfInter - 1.0) * sincqr, axis=1) * dr
            )
            self._outputData[f"xssf_total_{pair_str}"][:] = (
                self._outputData[f"xssf_intra_{pair_str}"][:]
                + self._outputData[f"xssf_inter_{pair_str}"][:]
            )

        self._outputData.add(
            "xssf_intra",
            "LineOutputVariable",
            (nq,),
            axis="q",
            units="au",
        )
        self._outputData.add(
            "xssf_inter",
            "LineOutputVariable",
            (nq,),
            axis="q",
            units="au",
        )
        self._outputData.add(
            "xssf_total",
            "LineOutputVariable",
            (nq,),
            axis="q",
            units="au",
            main_result=True,
        )

        asf = dict(
            (
                k,
                atomic_scattering_factor(
                    k,
                    self._outputData["q"],
                    self.configuration["trajectory"]["instance"],
                ),
            )
            for k in list(nAtomsPerElement.keys())
        )
        weight_dict = get_weights(asf, nAtomsPerElement, 2)
        assign_weights(self._outputData, weight_dict, "xssf_intra_%s%s")
        assign_weights(self._outputData, weight_dict, "xssf_inter_%s%s")
        assign_weights(self._outputData, weight_dict, "xssf_total_%s%s")
        xssfIntra = weighted_sum(self._outputData, weight_dict, "xssf_intra_%s%s")
        self._outputData["xssf_intra"][:] = xssfIntra

        xssfInter = weighted_sum(self._outputData, weight_dict, "xssf_inter_%s%s")
        self._outputData["xssf_inter"][:] = xssfInter

        self._outputData["xssf_total"][:] = xssfIntra + xssfInter

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
