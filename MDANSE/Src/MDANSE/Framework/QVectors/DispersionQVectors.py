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

import numpy as np
import numpy.typing as npt

from MDANSE.Framework.QVectors.IQVectors import IQVectors


def dispersion_vectors(
    q_start: npt.NDArray[float],
    q_end: npt.NDArray[float],
    q_step: float,
) -> tuple[npt.NDArray[float], npt.NDArray[float]]:
    """Generate vectors in a straight line.

    Vectors are generated on a line from q_start to q_end in steps of q_step.
    Additionally, q value for each step is returned. In an attempt to differentiate
    between positive and negative directions, the q values are given a sign
    depending on the projection of each vector onto the direction vector.

    Parameters
    ----------
    q_start : npt.NDArray[float]
        Starting point in reciprocal space.
    q_end : npt.NDArray[float]
        End point in reciprocal space.
    q_step : float
        Interval of |q| used for generating vectors.

    Returns
    -------
    tuple[npt.NDArray[float], npt.NDArray[float]]
        Q_vector array, array of dictionary keys to use in the generator.
    """
    distance = np.linalg.norm(q_end - q_start)
    normal = (q_end - q_start) / distance
    nSteps = int(distance / q_step)

    vects = (
        np.array(q_start)[:, np.newaxis]
        + np.outer(normal, np.arange(0, nSteps)) * q_step
    )

    dists = np.linalg.norm(vects, axis=0)
    return vects, dists * np.sign(np.dot(normal, vects))


class DispersionQVectors(IQVectors):
    """Generates Q vectors along a path between two points.

    As opposed to DispersionLatticeQVectors, the vectors will not
    necessarily correspond to integer HKL values.
    """

    settings = {}
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
            "default": [1, 0, 0],
        },
    )
    settings["q_step"] = (
        "FloatConfigurator",
        {"label": "Q step (nm^-1)", "mini": 1.0e-6, "default": 0.1},
    )

    def _generate(self):
        q_start = self._configuration["q_start"]["value"].array
        q_end = self._configuration["q_end"]["value"].array
        q_step = self._configuration["q_step"]["value"]
        if np.allclose(q_start, q_end):
            self._configuration[
                "q_end"
            ].error_status = "Zero-length vector cannot be used here"
            return

        q_vectors, keyvals = dispersion_vectors(q_start, q_end, q_step)
        if self._status is not None:
            self._status.start(len(keyvals))
        hkls = (
            self.qvectors_to_hkl(q_vectors, self._unit_cell)
            if self._unit_cell is not None
            else None
        )
        self._configuration["q_vectors"] = {}

        for index, keyval in enumerate(keyvals):
            self._configuration["q_vectors"][keyval] = {
                "q": keyval,
                "q_vectors": q_vectors[:, index][:, np.newaxis],
                "n_q_vectors": 1,
                "weights": np.ones(1),
                "hkls": hkls[:, index][:, np.newaxis] if hkls is not None else None,
            }
            if self._status is not None:
                if self._status.is_stopped():
                    return
                self._status.update()
