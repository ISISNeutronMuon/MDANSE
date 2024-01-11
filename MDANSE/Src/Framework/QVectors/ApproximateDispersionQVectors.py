# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/ApproximateDispersionLatticeQVectors.py
# @brief     Implements module/class/test ApproximateDispersionLatticeQVectors
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import itertools
import operator

import numpy as np

from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class ApproximateDispersionQVectors(LatticeQVectors):
    """ """

    settings = collections.OrderedDict()
    settings["q_start"] = (
        "VectorConfigurator",
        {
            "label": "Q start (nm^-1)",
            "valueType": float,
            "notNull": False,
            "default": [0, 0, 0],
        },
    )
    settings["q_end"] = (
        "VectorConfigurator",
        {
            "label": "Q end (nm^-1)",
            "valueType": float,
            "notNull": False,
            "default": [0, 0, 0],
        },
    )
    settings["q_step"] = (
        "FloatConfigurator",
        {"label": "Q step (nm^-1)", "mini": 1.0e-6, "default": 0.1},
    )

    def _generate(self):
        qStart = self._configuration["q_start"]["value"]
        qEnd = self._configuration["q_end"]["value"]
        qStep = self._configuration["q_step"]["value"]

        d = (qEnd - qStart).length()

        n = (qEnd - qStart).normal()
        nSteps = int(d / qStep) + 1

        vects = (
            np.array(qStart)[:, np.newaxis] + np.outer(n, np.arange(0, nSteps)) * qStep
        )

        hkls = np.rint(np.dot(self._directUnitCell, vects))

        dists = np.sqrt(np.sum(vects**2, axis=0))
        dists = zip(range(len(dists)), dists)
        dists.sort(key=operator.itemgetter(1))
        qGroups = itertools.groupby(dists, key=operator.itemgetter(1))
        qGroups = collections.OrderedDict(
            [(k, [item[0] for item in v]) for k, v in qGroups]
        )

        if self._status is not None:
            self._status.start(len(qGroups))

        self._configuration["q_vectors"] = collections.OrderedDict()

        for k, v in qGroups.items():
            self._configuration["q_vectors"][k] = {}
            self._configuration["q_vectors"][k]["q"] = k
            self._configuration["q_vectors"][k]["q_vectors"] = vects[:, v]
            self._configuration["q_vectors"][k]["n_q_vectors"] = len(v)
            self._configuration["q_vectors"][k]["hkls"] = hkls[:, v]

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()
