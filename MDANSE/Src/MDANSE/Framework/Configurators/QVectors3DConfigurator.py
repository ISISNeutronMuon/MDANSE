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
        "u": (1.0, 0.0, 0.0),
        "v": (0.0, 1.0, 0.0),
        "w": (0.0, 0.0, 1.0),
        "u_range": (-5.0, 5.0, 1.0),
        "v_range": (-5.0, 5.0, 1.0),
        "w_range": (-5.0, 5.0, 1.0),
    }
    _configurators_classes = {
        "seed": partial(IntegerConfigurator, mini=0),
        "n_samples": partial(IntegerConfigurator, mini=1),
        "force_equal_weights": partial(BooleanConfigurator),
        "supercell_used": partial(
            VectorConfigurator, valueType=int, notNull=True, mini=1
        ),
        "u": partial(VectorConfigurator, valueType=float, notNull=True),
        "v": partial(VectorConfigurator, valueType=float, notNull=True),
        "w": partial(VectorConfigurator, valueType=float, notNull=True),
        "u_range": partial(RangeConfigurator, valueType=float, includeLast=True),
        "v_range": partial(RangeConfigurator, valueType=float, includeLast=True),
        "w_range": partial(RangeConfigurator, valueType=float, includeLast=True),
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
        self["u"] = np.array(value["u"])
        self["v"] = np.array(value["v"])
        self["w"] = np.array(value["w"])

        # transform from uvw of the subcell to hkl of the cell
        # e.g. hkl_cell_coords = self["transform"] @ uvw_subcell_coords
        self["transform"] = (
            np.column_stack((self["u"], self["v"], self["w"])) * self["sc_used"]
        )

        if np.linalg.det(self["transform"]) == 0.0:
            self.error_status = "The input uvw vectors are not linearly independent."
            return

        self["u_range"] = self["configurators"]["u_range"]["value"]
        self["v_range"] = self["configurators"]["v_range"]["value"]
        self["w_range"] = self["configurators"]["w_range"]["value"]

        self["min_uvw"] = np.array(
            [self["u_range"][0], self["v_range"][0], self["w_range"][0]]
        )
        self["max_uvw"] = np.array(
            [self["u_range"][-1], self["v_range"][-1], self["w_range"][-1]]
        )
        self["step_uvw"] = np.array(
            [value["u_range"][2], value["v_range"][2], value["w_range"][2]]
        )

        # find the max_hkl for the fft, we want it to be larger than
        # the padded uvw grid
        max_hkl = np.zeros(3, dtype=int)
        for point in it.product(
            *zip(
                self["min_uvw"] - 2 * self["step_uvw"],
                self["max_uvw"] + 2 * self["step_uvw"],
                strict=False,
            )
        ):
            hkl = np.dot(self["transform"], point)
            max_hkl = np.maximum(max_hkl, np.ceil(np.abs(hkl)).astype(int))
        self["max_hkl"] = max_hkl + 1

        # the dimensions of the output results
        self["gdim_uvw"] = np.array(
            [
                self["u_range"].shape[0],
                self["v_range"].shape[0],
                self["w_range"].shape[0],
            ]
        )

        self.error_status = "OK"
