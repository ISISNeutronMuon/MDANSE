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
from MDANSE.Mathematics.Arithmetic import weight


class StaticStructureFactor(DistanceHistogram):
    """
    Computes the static structure factor from the pair distribution function for a set of atoms.
    The result is defined as S(q) = F_coh(q, t = 0).
    """

    label = "Static Structure Factor"

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
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "b_coherent",
            "dependencies": {
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        frame_index = self.configuration["frames"]["value"][0]

        conf = self.configuration["trajectory"]["instance"].configuration(frame_index)
        try:
            cell_volume = conf.unit_cell.volume
        except:
            raise ValueError(
                "Static Structure Factor cannot be computed for chemical system without a defined simulation box"
            )
        if abs(cell_volume) < 1e-11:
            raise ValueError(
                f"Non-physical unit cell volume: {cell_volume}. Static Structure Factor will not be calculated."
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
            self._outputData.add(
                "ssf_intra_%s%s" % pair,
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
            )
            self._outputData.add(
                "ssf_inter_%s%s" % pair,
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
            )
            self._outputData.add(
                "ssf_total_%s%s" % pair,
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
            )

            ni = nAtomsPerElement[pair[0]]
            nj = nAtomsPerElement[pair[1]]

            idi = self.selectedElements.index(pair[0])
            idj = self.selectedElements.index(pair[1])

            if pair[0] == pair[1]:
                nij = ni * (ni - 1) / 2.0
            else:
                nij = ni * nj
                self.hIntra[idi, idj] += self.hIntra[idj, idi]
                self.hInter[idi, idj] += self.hInter[idj, idi]

            fact = nij * nFrames * shellVolumes

            pdfIntra = self.hIntra[idi, idj, :] / fact
            pdfInter = self.hInter[idi, idj, :] / fact

            self._outputData["ssf_intra_%s%s" % pair][:] = (
                fact1 * np.sum((r**2) * pdfIntra * sincqr, axis=1) * dr
            )
            self._outputData["ssf_inter_%s%s" % pair][:] = (
                1.0 + fact1 * np.sum((r**2) * (pdfInter - 1.0) * sincqr, axis=1) * dr
            )
            self._outputData["ssf_total_%s%s" % pair][:] = (
                self._outputData["ssf_intra_%s%s" % pair][:]
                + self._outputData["ssf_inter_%s%s" % pair][:]
            )

        self._outputData.add(
            "ssf_intra", "LineOutputVariable", (nq,), axis="q", units="au"
        )
        self._outputData.add(
            "ssf_inter",
            "LineOutputVariable",
            (nq,),
            axis="q",
            units="au",
        )
        self._outputData.add(
            "ssf_total", "LineOutputVariable", (nq,), axis="q", units="au"
        )

        weights = self.configuration["weights"].get_weights()

        ssfIntra = weight(
            weights, self._outputData, nAtomsPerElement, 2, "ssf_intra_%s%s"
        )
        self._outputData["ssf_intra"][:] = ssfIntra

        ssfInter = weight(
            weights, self._outputData, nAtomsPerElement, 2, "ssf_inter_%s%s"
        )

        self._outputData["ssf_inter"][:] = ssfInter

        self._outputData["ssf_total"][:] = ssfIntra + ssfInter

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
