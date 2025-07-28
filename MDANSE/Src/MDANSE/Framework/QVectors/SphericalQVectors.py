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
from MDANSE.Mathematics.Geometry import random_points_on_sphere


class SphericalQVectors(IQVectors):
    """Generates vectors randomly on a sphere.

    Vectors within one shell are generated within
    a tolerance limit around a central |Q| value.
    Most calculations will produce one data point
    for |Q| by averaging the results over all
    vectors in the shell.
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
    settings["width"] = ("FloatConfigurator", {"mini": 0.0, "default": 1.0})

    def _generate(self):
        if self._configuration["seed"]["value"] != 0:
            np.random.seed(self._configuration["seed"]["value"])

        width = self._configuration["width"]["value"]

        nVectors = self._configuration["n_vectors"]["value"]

        self._configuration["q_vectors"] = collections.OrderedDict()

        if self._status is not None:
            self._status.start(len(self._configuration["shells"]["value"]))

        for q in self._configuration["shells"]["value"]:
            fact = q * np.sign(
                np.random.uniform(-0.5, 0.5, nVectors)
            ) + width * np.random.uniform(-0.5, 0.5, nVectors)

            v = random_points_on_sphere(radius=1.0, nPoints=nVectors)

            self._configuration["q_vectors"][q] = {}
            self._configuration["q_vectors"][q]["q_vectors"] = fact * v
            self._configuration["q_vectors"][q]["n_q_vectors"] = nVectors
            self._configuration["q_vectors"][q]["q"] = q
            self._configuration["q_vectors"][q]["hkls"] = None

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
