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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator

from .BooleanConfigurator import BooleanConfigurator
from .IntegerConfigurator import IntegerConfigurator
from .RangeConfigurator import RangeConfigurator
from .VectorConfigurator import VectorConfigurator


@IConfigurator.register("QVectors3DConfigurator")
class QVectors3DConfigurator(IConfigurator):
    _default = {
        "seed": 0,
        "n_samples": 1000,
        "force_equal_weights": False,
        "supercell_used": (1, 1, 1),
        "q1": (1.0, 0.0, 0.0),
        "q2": (0.0, 1.0, 0.0),
        "q3": (0.0, 0.0, 1.0),
        "q1_range": (-5.0, 5.0, 1.0),
        "q2_range": (-5.0, 5.0, 1.0),
        "q3_range": (-5.0, 5.0, 1.0),
    }
    _configurators_classes = {
        "seed": partial(IntegerConfigurator, mini=0),
        "n_samples": partial(IntegerConfigurator, mini=1),
        "force_equal_weights": partial(BooleanConfigurator),
        "supercell_used": partial(
            VectorConfigurator, valueType=int, notNull=True, mini=1
        ),
        "q1": partial(VectorConfigurator, valueType=float, notNull=True),
        "q2": partial(VectorConfigurator, valueType=float, notNull=True),
        "q3": partial(VectorConfigurator, valueType=float, notNull=True),
        "q1_range": partial(RangeConfigurator, valueType=float, includeLast=True),
        "q2_range": partial(RangeConfigurator, valueType=float, includeLast=True),
        "q3_range": partial(RangeConfigurator, valueType=float, includeLast=True),
    }

    label = "3D Q vector generator"
    tooltip = "Generates Q vectors in a slice with a finite thickness"

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
            self.error_status = f"Errors configuring settings: {error_statuses}"
            return

        self["seed"] = self["configurators"]["seed"]["value"]
        self["n_samples"] = self["configurators"]["n_samples"]["value"]

        self["sc_used"] = np.array(value["supercell_used"])
        self["q1"] = np.array(value["q1"])
        self["q2"] = np.array(value["q2"])
        self["q3"] = np.array(value["q3"])

        # transform from q1, q2, q3 basis vectors of the reciprocal subcell to the
        # basis vectors of the reciprocal cell
        self["transform"] = (
            np.column_stack((self["q1"], self["q2"], self["q3"])) * self["sc_used"]
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

        self.error_status = "OK"
