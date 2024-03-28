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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)
from MDANSE.Framework.Projectors.IProjector import IProjector
from MDANSE.Framework.Projectors.IProjector import ProjectorError


class ProjectionConfigurator(IConfigurator):
    """
    This configurator allows to define a projector for atomic coordinates.

    Planar and axial projections are supported by MDANSE while a null projector, that does not project the coordinates, has been introduced
    in MDANSE.Framework.Projectors.IProjector.IProjector for the sake of homogeneity.
    """

    _default = None

    def configure(self, value):
        """
        Configure a projector. 
                
        :param value: the input projector definition. It can be a 2-tuple whose 1st element if the name \
        of the projector (one of *'null'*,*'axial'* or *'planar'*) and the 2nd element the parameters for the selected \
        projector (None for *'null'*, a Scientific.Vector for *'axial'* and a list of two Scientific.Vector for *'planar'*) \
        or ``None`` in the case where no projection is needed.
        :type value: 2-tuple
        """
        self["axis"] = None

        if value is None:
            value = ("NullProjector", None)

        try:
            mode, axis = value
        except (TypeError, ValueError) as e:
            self.error_status = "Failed to unpack input" + str(e)
            return

        if not isinstance(mode, str):
            self.error_status = "invalid type for projection mode: must be a string"
            return

        try:
            self["projector"] = IProjector.create(mode)
        except KeyError:
            self.error_status = f"the projector {mode} is unknown"
            return
        else:
            try:
                self["projector"].set_axis(axis)
            except ProjectorError:
                self.error_status = f"Axis {axis} is wrong for this projector"
                return
            else:
                self["axis"] = self["projector"].axis
        self.error_status = "OK"

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        if self["axis"] is not None:
            return "No projection performed\n"
        else:
            return "Projection along %r axis\n" % self["axis"]
