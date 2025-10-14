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

import traceback

from qtpy.QtCore import Slot

from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import (
    chemical_system_summary,
    trajectory_summary,
)

from .TextInfo import TextInfo


class TrajectoryInfo(TextInfo):
    @Slot(object)
    def update_panel(self, data: tuple):
        fullpath, incoming = data
        if incoming is None:
            self.setHtml(self.filter(fullpath))
            return
        try:
            text = trajectory_summary(incoming)  # this is from a trajectory object
        except AttributeError as err:
            LOG.error(
                "Could not summarise trajectory %s.\n Error: %s.\n Traceback: %s",
                incoming,
                err,
                traceback.format_exc(),
            )
            self.setHtml("")
            return
        try:
            cs = incoming.chemical_system
        except AttributeError:
            LOG.error("Trajectory %s has no chemical system", incoming)
        else:
            text += chemical_system_summary(cs)
        filtered = self.filter(text)
        self.setHtml(filtered)
