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
from typing import Any

import numpy as np

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


@IConfigurator.register("QVectors3DConfigurator")
class QVectors3DConfigurator(IConfigurator):

    _default = {
        "seed": 0,
        "n_samples": 50000,
        "force_equal_weights": False,
        "supercell_used": (1, 1, 1),
        # "u": order, q_x, q_y, q_z, q_min, q_max, width
        "u": (1.0, 0.0, 0.0, -5.0, 5.0, 1.0),
        "v": (0.0, 1.0, 0.0, -5.0, 5.0, 1.0),
        "w": (0.0, 0.0, 1.0, -5.0, 5.0, 1.0),
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

        self["u"] = value["u"]
        self["v"] = value["v"]
        self["w"] = value["w"]
        self["u_vec"] = np.array([value["u"][0], value["u"][1], value["u"][2]])
        self["u_min"] = value["u"][3]
        self["u_max"] = value["u"][3]
        self["u_step"] = value["u"][3]
        self["v_vec"] = np.array([value["v"][0], value["v"][1], value["v"][2]])
        self["v_min"] = value["v"][3]
        self["v_max"] = value["v"][3]
        self["v_step"] = value["v"][3]
        self["w_vec"] = np.array([value["w"][0], value["w"][1], value["w"][2]])
        self["w_min"] = value["w"][3]
        self["w_max"] = value["w"][3]
        self["w_step"] = value["w"][3]

        transform = np.array([self["u_vec"], self["v_vec"], self["w_vec"]]).T

        self["n_samples"] = value["n_samples"]
        self["seed"] = value["seed"]
        self["force_equal_weights"] = value["force_equal_weights"]
        self["sc_used"] = np.array(value["supercell_used"])

        max_hkl = np.zeros(3, dtype=int)
        for point in it.product(
            *zip(
                [self["u_min"], self["v_min"], self["w_min"]],
                [self["u_max"], self["v_max"], self["w_max"]],
                strict=False)
        ):
            hkl = np.dot(transform, point) / self["sc_used"]
            max_hkl = np.maximum(max_hkl, np.ceil(np.abs(hkl)).astype(int))

        self["max_hkl"] = max_hkl
