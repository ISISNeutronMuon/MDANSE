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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now

import collections

import numpy as np


from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram


class CoordinationNumber(DistanceHistogram):
    """
    The Coordination Number is computed from the pair distribution function for a set of atoms.
    It describes the total number of neighbours, as a function of distance, from a central atom, or the centre of a group of atoms.
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
        "RangeConfigurator",
        {"valueType": float, "includeLast": True, "mini": 0.0},
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

        npoints = len(self.configuration["r_values"]["mid_points"])

        self._outputData.add(
            "r",
            "LineOutputVariable",
            self.configuration["r_values"]["mid_points"],
            units="nm",
        )

        for pair in self._elementsPairs:
            invPair = pair[::-1]
            self._outputData.add(
                "cn_intra_%s%s" % pair,
                "LineOutputVariable",
                (npoints,),
                axis="r",
                units="au",
            )
            self._outputData.add(
                "cn_inter_%s%s" % pair,
                "LineOutputVariable",
                (npoints,),
                axis="r",
                units="au",
            )
            self._outputData.add(
                "cn_total_%s%s" % pair,
                "LineOutputVariable",
                (npoints,),
                axis="r",
                units="au",
            )
            self._outputData.add(
                "cn_intra_%s%s" % invPair,
                "LineOutputVariable",
                (npoints,),
                axis="r",
                units="au",
            )
            self._outputData.add(
                "cn_inter_%s%s" % invPair,
                "LineOutputVariable",
                (npoints,),
                axis="r",
                units="au",
            )
            self._outputData.add(
                "cn_total_%s%s" % invPair,
                "LineOutputVariable",
                (npoints,),
                axis="r",
                units="au",
            )

        nFrames = self.configuration["frames"]["number"]

        densityFactor = 4.0 * np.pi * self.configuration["r_values"]["mid_points"]

        shellSurfaces = densityFactor * self.configuration["r_values"]["mid_points"]

        shellVolumes = shellSurfaces * self.configuration["r_values"]["step"]

        self.averageDensity *= 4.0 * np.pi / nFrames

        r2 = self.configuration["r_values"]["mid_points"] ** 2
        dr = self.configuration["r_values"]["step"]

        for k in list(self._concentrations.keys()):
            self._concentrations[k] /= nFrames

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for pair in self._elementsPairs:
            at1, at2 = pair
            ni = nAtomsPerElement[at1]
            nj = nAtomsPerElement[at2]

            idi = self.selectedElements.index(at1)
            idj = self.selectedElements.index(at2)

            if idi == idj:
                nij = ni * (ni - 1) / 2.0
            else:
                nij = ni * nj
                self.hIntra[idi, idj] += self.hIntra[idj, idi]
                self.hInter[idi, idj] += self.hInter[idj, idi]

            fact = nij * nFrames * shellVolumes

            self.hIntra[idi, idj, :] /= fact
            self.hInter[idi, idj, :] /= fact

            cnIntra = np.add.accumulate(self.hIntra[idi, idj, :] * r2) * dr
            cnInter = np.add.accumulate(self.hInter[idi, idj, :] * r2) * dr
            cnTotal = cnIntra + cnInter

            cAlpha = self._concentrations[pair[0]]
            cBeta = self._concentrations[pair[1]]

            invPair = pair[::-1]

            self._outputData["cn_intra_%s%s" % pair][:] = (
                self.averageDensity * cBeta * cnIntra
            )
            self._outputData["cn_inter_%s%s" % pair][:] = (
                self.averageDensity * cBeta * cnInter
            )
            self._outputData["cn_total_%s%s" % pair][:] = (
                self.averageDensity * cBeta * cnTotal
            )
            self._outputData["cn_intra_%s%s" % invPair][:] = (
                self.averageDensity * cAlpha * cnIntra
            )
            self._outputData["cn_inter_%s%s" % invPair][:] = (
                self.averageDensity * cAlpha * cnInter
            )
            self._outputData["cn_total_%s%s" % invPair][:] = (
                self.averageDensity * cAlpha * cnTotal
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()

        DistanceHistogram.finalize(self)
