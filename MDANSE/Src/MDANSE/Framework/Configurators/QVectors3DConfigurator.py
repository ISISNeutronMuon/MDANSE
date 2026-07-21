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

import itertools as it
from functools import partial
from typing import Any

import numpy as np

from .IConfigurator import IConfigurator, PredictionSettings
from .IntegerConfigurator import IntegerConfigurator
from .QVectors3DVectorConfigurator import QVectors3DVectorConfigurator
from .RangeConfigurator import RangeConfigurator
from .VectorConfigurator import VectorConfigurator


@IConfigurator.register("QVectors3DConfigurator")
class QVectors3DConfigurator(IConfigurator):
    _default = {
        "seed": 0,
        "n_samples": 100,
        "supercell_used": (1, 1, 1),
        "q1": (1.0, 0.0, 0.0),
        "q2": (0.0, 1.0, 0.0),
        "q3": "q1 x q2",
        "q1_range": (-3.0, 3.0, 1.0),
        "q2_range": (-3.0, 3.0, 1.0),
        "q3_range": (-3.0, 3.0, 1.0),
    }
    _configurators_classes = {
        "seed": partial(IntegerConfigurator, mini=0),
        "n_samples": partial(IntegerConfigurator, mini=1),
        "supercell_used": partial(
            VectorConfigurator, valueType=int, notNull=True, mini=1
        ),
        "q1": partial(
            QVectors3DVectorConfigurator,
            valueType=float,
            notNull=True,
            other_vec_1="q2",
            other_vec_2="q3",
        ),
        "q2": partial(
            QVectors3DVectorConfigurator,
            valueType=float,
            notNull=True,
            other_vec_1="q1",
            other_vec_2="q3",
        ),
        "q3": partial(
            QVectors3DVectorConfigurator,
            valueType=float,
            notNull=True,
            other_vec_1="q1",
            other_vec_2="q2",
        ),
        "q1_range": partial(RangeConfigurator, valueType=float, includeLast=True),
        "q2_range": partial(RangeConfigurator, valueType=float, includeLast=True),
        "q3_range": partial(RangeConfigurator, valueType=float, includeLast=True),
    }

    label = "3D Q vector generator"
    tooltip = "Generates Q vectors in slices with a finite thickness"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prediction = PredictionSettings(
            key="q", label="3D Q vector generator", unit="rlu"
        )

    def configure(self, value: dict[str, Any]):
        """Create a 3D vector generator with given parameters.

        Parameters
        ----------
        value : tuple[str, dict[str, Any]]
            Class name and dictionary of input parameters

        """
        if not self.update_needed(value):
            return

        self._original_input = value

        uc = self.configurable[self.dependencies["trajectory"]]["instance"].unit_cell(0)
        if uc is None:
            self.error_status = (
                f"Cannot generate q-vectors for a system without a unit cell."
            )
            return

        # use the configurators to do all the error checking for us
        self["configurators"] = {}
        error_statuses = {}
        for key, val in self._configurators_classes.items():
            configurator = val(key)
            configurator.configure(value[key])
            if configurator.error_status != "OK":
                error_statuses[key] = configurator.error_status
            self["configurators"][key] = configurator

        if error_statuses:
            self.error_status = f"Errors configuring settings: {error_statuses}."
            return

        if (
            sum(
                self["configurators"][vec]["cross_product"]
                for vec in ("q1", "q2", "q3")
            )
            > 1
        ):
            self.error_status = "Only one basis vector can be defined as a cross product of the other two."
            return

        self["seed"] = self["configurators"]["seed"]["value"]
        self["n_samples"] = self["configurators"]["n_samples"]["value"]

        self["sc_used"] = np.array(value["supercell_used"])

        for q in ("q1", "q2", "q3"):
            if not self["configurators"][q]["cross_product"]:
                self[q] = np.array(value[q])
            else:
                q_a, _, q_b = value[q].split(" ")
                self[q] = np.cross(np.array(value[q_a]), np.array(value[q_b]))

        # transform from q1, q2, q3 basis vectors of the reciprocal subcell to the
        # basis vectors of the reciprocal cell
        self["transform"] = (
            np.column_stack((self["q1"], self["q2"], self["q3"]))
            * self["sc_used"][:, None]
        )

        if np.linalg.det(self["transform"]) == 0.0:
            self.error_status = (
                "The input basis vectors, q1, q2, and q3 are not linearly independent."
            )
            return

        self["q1_range"] = self["configurators"]["q1_range"]["value"]
        self["q2_range"] = self["configurators"]["q2_range"]["value"]
        self["q3_range"] = self["configurators"]["q3_range"]["value"]

        self["min_123"] = np.array(
            [self["q1_range"][0], self["q2_range"][0], self["q3_range"][0]]
        )
        self["max_123"] = np.array(
            [self["q1_range"][-1], self["q2_range"][-1], self["q3_range"][-1]]
        )
        self["step_123"] = np.array(
            [value["q1_range"][2], value["q2_range"][2], value["q3_range"][2]]
        )

        # the dimensions of the output results
        self["gdim_123"] = np.array(
            [
                self["q1_range"].shape[0],
                self["q2_range"].shape[0],
                self["q3_range"].shape[0],
            ]
        )

        # find the max_hkl of the reciprocal cell for the fft, we want it to
        # be larger than the padded grid with the q1, q2, q3 basis vectors
        self["max_hkl"] = np.zeros(3, dtype=int)
        for point in it.product(
            *zip(
                self["min_123"] - self["step_123"],
                self["max_123"] + self["step_123"],
                strict=False,
            )
        ):
            hkl = np.dot(self["transform"], point)
            self["max_hkl"] = np.maximum(
                self["max_hkl"], np.ceil(np.abs(hkl)).astype(int)
            )

        aliases = {
            "q1 basis vector": "q1",
            "q2 basis vector": "q2",
            "q3 basis vector": "q3",
            "q1 range": "q1_range",
            "q2 range": "q2_range",
            "q3 range": "q3_range",
        }

        self.prediction_keys = list(aliases.keys())
        for k, v in aliases.items():
            self[k] = self[v]

        self.error_status = "OK"
