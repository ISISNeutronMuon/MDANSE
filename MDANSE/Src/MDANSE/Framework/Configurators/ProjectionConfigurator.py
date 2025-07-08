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

from collections.abc import Sequence
from typing import SupportsFloat

import numpy as np

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Projectors.IProjector import IProjector, ProjectorError


class ProjectionConfigurator(IConfigurator):
    """Projects atomic coordinates onto an axis or plane.

    Null projector (which does nothing) is the standard choice.
    The input vector can be used as an axis direction,
    or as a plane normal vector.

    """

    _default = None

    def configure(self, value: tuple[str, Sequence[SupportsFloat]]):
        """
        Configure a projector.

        :param value: the input projector definition. It can be a 2-tuple whose 1st element if the name \
        of the projector (one of *'null'*,*'axial'* or *'planar'*) and the 2nd element the parameters for the selected \
        projector (None for *'null'*, a Scientific.Vector for *'axial'* and a list of two Scientific.Vector for *'planar'*) \
        or ``None`` in the case where no projection is needed.
        :type value: 2-tuple
        """
        if not self.update_needed(value):
            return

        self["axis"] = None
        self._original_input = value

        if value is None:
            value = ("NullProjector", ())

        try:
            try:
                mode, axis = value
            except (TypeError, ValueError) as e:
                raise Exception("Failed to unpack input" + str(e))

            if not isinstance(mode, str):
                raise Exception("invalid type for projection mode: must be a string")

            try:
                self["projector"] = IProjector.create(mode)
            except KeyError:
                raise Exception(f"the projector {mode} is unknown")

            if mode == "NullProjector":
                self.error_status = "OK"
                return

            try:
                vector = [float(x) for x in axis]
            except ValueError:
                raise Exception(f"Could not convert {axis} to numbers")

            if np.allclose(vector, 0):
                raise Exception("Vector of 0 length does not define projection")

            try:
                self["projector"].set_axis(vector)
            except ProjectorError:
                raise Exception(f"Axis {vector} is wrong for this projector")

            self["axis"] = self["projector"].axis

        except Exception as err:
            self.error_status = str(err)
            return

        self.error_status = "OK"
