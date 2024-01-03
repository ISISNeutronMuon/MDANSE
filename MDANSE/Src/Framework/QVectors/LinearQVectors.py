# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/QVectors/LinearQVectors.py
# @brief     Implements module/class/test LinearQVectors
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

from MDANSE.Framework.QVectors.IQVectors import IQVectors


class LinearQVectors(IQVectors):
    """ """

    settings = collections.OrderedDict()
    settings["seed"] = ("IntegerConfigurator", {"mini": 0, "default": 0})
    settings["shells"] = (
        "RangeConfigurator",
        {
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "default": (0, 5.0, 0.5),
        },
    )
    settings["n_vectors"] = ("IntegerConfigurator", {"mini": 1, "default": 50})
    settings["width"] = ("FloatConfigurator", {"mini": 1.0e-6, "default": 1.0})
    settings["axis"] = (
        "VectorConfigurator",
        {"normalize": True, "notNull": True, "default": [1, 0, 0]},
    )

    def _generate(self):
        if self._configuration["seed"]["value"] != 0:
            np.random.seed(self._configuration["seed"]["value"])

        axis = self._configuration["axis"]["vector"]

        width = self._configuration["width"]["value"]

        nVectors = self._configuration["n_vectors"]["value"]

        if self._status is not None:
            self._status.start(self._configuration["shells"]["number"])

        self._configuration["q_vectors"] = collections.OrderedDict()

        for q in self._configuration["shells"]["value"]:
            fact = q * np.sign(
                np.random.uniform(-0.5, 0.5, nVectors)
            ) + width * np.random.uniform(-0.5, 0.5, nVectors)

            self._configuration["q_vectors"][q] = {}
            self._configuration["q_vectors"][q]["q_vectors"] = (
                axis.array[:, np.newaxis] * fact
            )
            self._configuration["q_vectors"][q]["n_q_vectors"] = nVectors
            self._configuration["q_vectors"][q]["q"] = q
            self._configuration["q_vectors"][q]["hkls"] = None

            if self._status is not None:
                if self._status.is_stopped():
                    return
                else:
                    self._status.update()
