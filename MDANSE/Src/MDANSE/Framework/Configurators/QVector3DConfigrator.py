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

from typing import Any

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


@IConfigurator.register("QVectors3DConfigurator")
class QVectors3DConfigurator(IConfigurator):

    _default = {
        "seed": 0,
        "n_samples": 50000,
        "force_equal_weights": False,
        # "u": order, q_x, q_y, q_z, q_min, q_max, step
        "u": (0, 1.0, 0.0, 0.0, -5.0, 5.0, 1.0),
        "v": (1, 0.0, 1.0, 0.0, -5.0, 5.0, 1.0),
        "w": (2, 0.0, 0.0, 1.0, -5.0, 5.0, 1.0),
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
        self["n_samples"] = value["n_samples"]
        self["seed"] = value["seed"]
        self["force_equal_weights"] = value["force_equal_weights"]