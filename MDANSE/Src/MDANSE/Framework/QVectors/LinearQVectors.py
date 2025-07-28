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
from __future__ import annotations

import collections

import numpy as np

from MDANSE.Framework.QVectors.IQVectors import IQVectors


class LinearQVectors(IQVectors):
    """Generates vectors randomly on a straight line.

    Vectors within one shell are generated within
    a tolerance limit around a central |Q| value.
    Most calculations will produce one data point
    for |Q| by averaging the results over all
    vectors in the group, which is still called
    a shell.
    """

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
        {"normalize": True, "notNull": True, "default": [1, 0, 0], "valueType": float},
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
                self._status.update()
