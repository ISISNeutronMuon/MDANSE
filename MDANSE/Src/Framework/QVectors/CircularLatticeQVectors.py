# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/CircularLatticeQVectors.py
# @brief     Implements module/class/test CircularLatticeQVectors
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


class CircularLatticeQVectors(LatticeQVectors):
    """ """

    settings = collections.OrderedDict()
    settings["seed"] = ("integer", {"mini": 0, "default": 0})
    settings["shells"] = (
        "range",
        {"valueType": float, "includeLast": True, "mini": 0.0},
    )
    settings["n_vectors"] = ("integer", {"mini": 1, "default": 50})
    settings["width"] = ("float", {"mini": 1.0e-6, "default": 1.0})
    settings["axis_1"] = (
        "vector",
        {"normalize": False, "notNull": True, "valueType": int, "default": [1, 0, 0]},
    )
    settings["axis_2"] = (
        "vector",
        {"normalize": False, "notNull": True, "valueType": int, "default": [0, 1, 0]},
    )

    def _generate(self):
        if self._configuration["seed"]["value"] != 0:
            np.random.seed(self._configuration["seed"]["value"])
            random.seed(self._configuration["seed"]["value"])

        hkls = np.transpose(
            [
                self._configuration["axis_1"]["vector"],
                self._configuration["axis_2"]["vector"],
            ]
        )

        qVects = np.dot(self._inverseUnitCell, hkls)

        qMax = (
            self._configuration["shells"]["last"]
            + 0.5 * self._configuration["width"]["value"]
        )

        uvMax = np.ceil([qMax / Vector(v).length() for v in qVects.T]) + 1
        # Enforce integers in uvMax
        uvMax = uvMax.astype(np.int64)

        idxs = np.mgrid[-uvMax[0] : uvMax[0] + 1, -uvMax[1] : uvMax[1] + 1]

        idxs = idxs.reshape(2, (2 * uvMax[0] + 1) * (2 * uvMax[1] + 1))

        vects = np.dot(qVects, idxs)

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


REGISTRY["circular_lattice"] = CircularLatticeQVectors
