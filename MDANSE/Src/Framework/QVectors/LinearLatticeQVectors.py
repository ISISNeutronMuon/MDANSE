# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/LinearLatticeQVectors.py
# @brief     Implements module/class/test LinearLatticeQVectors
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import random

import numpy as np

from MDANSE.Mathematics.LinearAlgebra import Vector

from MDANSE import REGISTRY
from MDANSE.Framework.QVectors.LatticeQvectors import LatticeQVectors


class LinearLatticeQVectors(LatticeQVectors):
    """ """

    settings = collections.OrderedDict()
    settings["seed"] = ("integer", {"mini": 0, "default": 0})
    settings["shells"] = (
        "range",
        {
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "default": (0, 5.0, 0.5),
        },
    )
    settings["n_vectors"] = ("integer", {"mini": 1, "default": 50})
    settings["width"] = ("float", {"mini": 1.0e-6, "default": 1.0})
    settings["axis"] = (
        "vector",
        {"normalize": False, "notNull": True, "valueType": int, "default": [1, 0, 0]},
    )

    def _generate(self):
        if self._configuration["seed"]["value"] != 0:
            np.random.seed(self._configuration["seed"]["value"])
            random.seed(self._configuration["seed"]["value"])

        # The Q vector corresponding to the input hkl.
        qVect = np.dot(self._inverseUnitCell, self._configuration["axis"]["vector"])

        qMax = (
            self._configuration["shells"]["last"]
            + 0.5 * self._configuration["width"]["value"]
        )

        uMax = np.ceil(qMax / Vector(qVect).length()) + 1

        idxs = np.mgrid[-uMax : uMax + 1]

        vects = np.dot(qVect[:, np.newaxis], idxs[np.newaxis, :])

        dists2 = np.sum(vects**2, axis=0)

        halfWidth = self._configuration["width"]["value"] / 2

        nVectors = self._configuration["n_vectors"]["value"]

        if self._status is not None:
            self._status.start(self._configuration["shells"]["number"])

        self._configuration["q_vectors"] = collections.OrderedDict()

        for q in self._configuration["shells"]["value"]:
            qmin = max(0, q - halfWidth)

            q2low = qmin * qmin
            q2up = (q + halfWidth) * (q + halfWidth)

            hits = np.where((dists2 >= q2low) & (dists2 <= q2up))[0]

            nHits = len(hits)

            if nHits != 0:
                n = min(nHits, nVectors)

                if nHits > nVectors:
                    hits = random.sample(hits, nVectors)

                self._configuration["q_vectors"][q] = {}
                self._configuration["q_vectors"][q]["q_vectors"] = vects[:, hits]
                self._configuration["q_vectors"][q]["n_q_vectors"] = n
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


REGISTRY["linear_lattice"] = LinearLatticeQVectors
