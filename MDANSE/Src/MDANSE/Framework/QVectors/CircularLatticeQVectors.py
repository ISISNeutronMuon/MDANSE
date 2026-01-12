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

import random

import numpy as np

from MDANSE.Framework.QVectors.CircularQVectors import (
    circle_of_vectors,
    circle_rotation_matrix,
)
from MDANSE.Framework.QVectors.LatticeQVectors import LatticeQVectors


class CircularLatticeQVectors(LatticeQVectors):
    """Generates Q vectors on a plane perpendicular to the 'axis' vector.

    Vectors are grouped into shells limited to the range of
    (q - width/2, q + width/2) around the shell centre q.

    Only vectors commensurate with the reciprocal space lattice will be generated.
    If more lattice vectors than requested are available in the requested range
    for a shell, a subset of the vectors will be selected with the probability
    given as a Gaussian function with FWHM of width/2 and centred on the |q|
    which is the nominal centre of the shell.

    |Q| values for which no valid vectors can be found are omitted in the output.
    """

    settings = {}
    settings["seed"] = ("IntegerConfigurator", {"mini": 0, "default": 0})
    settings["shells"] = (
        "RangeConfigurator",
        {
            "valueType": float,
            "includeLast": True,
            "mini": 0.0,
            "default": (0.0, 5.0, 0.5),
        },
    )
    settings["n_vectors"] = ("IntegerConfigurator", {"mini": 1, "default": 50})
    settings["width"] = ("FloatConfigurator", {"mini": 1.0e-6, "default": 1.0})
    settings["axis"] = (
        "VectorConfigurator",
        {"normalize": False, "notNull": True, "valueType": float, "default": [0, 0, 1]},
    )

    def _generate(self):
        if self._configuration["seed"]["value"] != 0:
            np.random.seed(self._configuration["seed"]["value"])
            random.seed(self._configuration["seed"]["value"])

        nvecs_per_shell = self._configuration["n_vectors"]["value"]
        target_circle_axis = self._configuration["axis"]["value"] / np.linalg.norm(
            self._configuration["axis"]["value"],
        )
        rot_mat = circle_rotation_matrix(target_circle_axis)

        width = self._configuration["width"]["value"] / 2

        if self._status is not None:
            self._status.start(self._configuration["shells"]["number"])

        self._configuration["q_vectors"] = {}

        for q in self._configuration["shells"]["value"]:
            q_vectors = circle_of_vectors(q, width, nvecs_per_shell, rot_mat=rot_mat)
            lattice_hkl_vectors, weights = self.lattice_vectors_with_weights(
                q_vectors,
                self._unit_cell,
            )
            selection = self.vectors_within_limits(
                self.hkl_to_qvectors(lattice_hkl_vectors, self._unit_cell),
                q_min=q - 0.5 * width,
                q_max=q + 0.5 * width,
            )
            weights = weights[selection]
            lattice_hkl_vectors = lattice_hkl_vectors.T[selection].T
            if not len(weights):
                self._configuration["q_vectors"][q] = None
                continue

            self._configuration["q_vectors"][q] = {
                "q_vectors": self.hkl_to_qvectors(lattice_hkl_vectors, self._unit_cell),
                "weights": weights,
                "n_q_vectors": np.sum(weights),
                "q": q,
                "hkls": lattice_hkl_vectors,
            }

            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
