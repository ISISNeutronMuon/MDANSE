#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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


class PyConnectivity:
    """At the moment MDANSE_GUI does not contain any checks for connectivity.
    The intended solution is to include a connectivity scanner in the
    trajectory converter.
    In the meantime, since the MolecularViewer expects a PyConnectivity object,
    this dummy has been created. It never finds any bonds.
    """

    def __init__(self, *args, **kwargs):
        pass

    def add_point(self, index: int, point: np.ndarray, radius: float) -> bool:
        return True

    def find_collisions(self, tolerance: float) -> dict:
        return {}

    def get_neighbour(self, point: np.ndarray) -> int:
        return 0
