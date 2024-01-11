# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/MillerIndicesQVectors.py
# @brief     Implements module/class/test MillerIndicesQVectors
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

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class MillerIndicesQVectors(LatticeQVectors):
    """ """

    settings = collections.OrderedDict()
    settings["shells"] = (
        "RangeConfigurator",
        {
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "default": (0, 5.0, 0.5),
        },
    )
    settings["width"] = ("FloatConfigurator", {"mini": 1.0e-6, "default": 1.0})
    settings["h"] = (
        "RangeConfigurator",
        {"includeLast": True, "default": (0, 8, 1), "valueType": int},
    )
    settings["k"] = (
        "RangeConfigurator",
        {"includeLast": True, "default": (0, 8, 1), "valueType": int},
    )
    settings["l"] = (
        "RangeConfigurator",
        {"includeLast": True, "default": (0, 8, 1), "valueType": int},
    )

    def _generate(self):
        hSlice = slice(
            self._configuration["h"]["first"],
            self._configuration["h"]["last"] + 1,
            self._configuration["h"]["step"],
        )
        kSlice = slice(
            self._configuration["k"]["first"],
            self._configuration["k"]["last"] + 1,
            self._configuration["k"]["step"],
        )
        lSlice = slice(
            self._configuration["l"]["first"],
            self._configuration["l"]["last"] + 1,
            self._configuration["l"]["step"],
        )

        # The hkl matrix (3,n_hkls)
        hkls = np.mgrid[hSlice, kSlice, lSlice]
        hkls = hkls.reshape(3, hkls.size / 3)

        # The k matrix (3,n_hkls)
        vects = np.dot(self._inverseUnitCell, hkls)

        dists2 = np.sum(vects**2, axis=0)

        halfWidth = self._configuration["width"]["value"] / 2

        if self._status is not None:
            self._status.start(len(self._configuration["shells"]["value"]))

        self._configuration["q_vectors"] = collections.OrderedDict()

        for q in self._configuration["shells"]["value"]:
            qmin = max(0, q - halfWidth)

            q2low = qmin * qmin
            q2up = (q + halfWidth) * (q + halfWidth)

            hits = np.where((dists2 >= q2low) & (dists2 <= q2up))[0]

            nHits = len(hits)

            if nHits != 0:
                self._configuration["q_vectors"][q] = {}
                self._configuration["q_vectors"][q]["q_vectors"] = vects[:, hits]
                self._configuration["q_vectors"][q]["n_q_vectors"] = nHits
                self._configuration["q_vectors"][q]["q"] = q
                self._configuration["q_vectors"][q]["hkls"] = np.rint(
                    np.dot(
                        self._directUnitCell,
                        self._configuration["q_vectors"][q]["q_vectors"],
                    )
                )

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()
