# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/XRayStaticStructureFactor.py
# @brief     Implements module/class/test XRayStaticStructureFactor
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Jobs.DistanceHistogram import DistanceHistogram
from MDANSE.Mathematics.Arithmetic import weight


def atomic_scattering_factor(element, qvalues):
    a = np.empty((4,), dtype=np.float64)
    a[0] = ATOMS_DATABASE[element]["xray_asf_a1"]
    a[1] = ATOMS_DATABASE[element]["xray_asf_a2"]
    a[2] = ATOMS_DATABASE[element]["xray_asf_a3"]
    a[3] = ATOMS_DATABASE[element]["xray_asf_a4"]

    b = np.empty((4,), dtype=np.float64)
    b[0] = ATOMS_DATABASE[element]["xray_asf_b1"]
    b[1] = ATOMS_DATABASE[element]["xray_asf_b2"]
    b[2] = ATOMS_DATABASE[element]["xray_asf_b3"]
    b[3] = ATOMS_DATABASE[element]["xray_asf_b4"]

    c = ATOMS_DATABASE[element]["xray_asf_c"]

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

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = ("FramesConfigurator", {"dependencies": {"trajectory": "trajectory"}})
    settings["r_values"] = (
        "RangeConfigurator",
        {"valueType": float, "includeLast": True, "mini": 0.0},
    )
    settings["q_values"] = (
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
    settings["output_files"] = ("OutputFilesConfigurator", {"formats": ["HDFFormat", "ASCIIFormat"]})
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
            "q", "LineOutputVariable", self.configuration["q_values"]["value"], units="1/nm"
        )

        q = self._outputData["q"]
        r = self.configuration["r_values"]["mid_points"]

        fact1 = 4.0 * np.pi * self.averageDensity

        sincqr = np.sinc(np.outer(q, r) / np.pi)

        dr = self.configuration["r_values"]["step"]

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for pair in self._elementsPairs:
            self._outputData.add(
                "xssf_intra_%s%s" % pair, "LineOutputVariable", (nq,), axis="q", units="au"
            )
            self._outputData.add(
                "xssf_inter_%s%s" % pair,
                "LineOutputVariable",
                (nq,),
                axis="q",
                units="au",
            )
            self._outputData.add(
                "xssf_total_%s%s" % pair, "LineOutputVariable", (nq,), axis="q", units="au"
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

            self._outputData["xssf_intra_%s%s" % pair][:] = (
                fact1 * np.sum((r**2) * pdfIntra * sincqr, axis=1) * dr
            )
            self._outputData["xssf_inter_%s%s" % pair][:] = (
                1.0 + fact1 * np.sum((r**2) * (pdfInter - 1.0) * sincqr, axis=1) * dr
            )
            self._outputData["xssf_total_%s%s" % pair][:] = (
                self._outputData["xssf_intra_%s%s" % pair][:]
                + self._outputData["xssf_inter_%s%s" % pair][:]
            )

        self._outputData.add("xssf_intra", "LineOutputVariable", (nq,), axis="q", units="au")
        self._outputData.add("xssf_inter", "LineOutputVariable", (nq,), axis="q", units="au")
        self._outputData.add("xssf_total", "LineOutputVariable", (nq,), axis="q", units="au")

        asf = dict(
            (k, atomic_scattering_factor(k, self._outputData["q"]))
            for k in list(nAtomsPerElement.keys())
        )

        xssfIntra = weight(
            asf, self._outputData, nAtomsPerElement, 2, "xssf_intra_%s%s"
        )
        self._outputData["xssf_intra"][:] = xssfIntra

        xssfInter = weight(
            asf, self._outputData, nAtomsPerElement, 2, "xssf_inter_%s%s"
        )
        self._outputData["xssf_inter"][:] = xssfInter

        self._outputData["xssf_total"][:] = xssfIntra + xssfInter

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
