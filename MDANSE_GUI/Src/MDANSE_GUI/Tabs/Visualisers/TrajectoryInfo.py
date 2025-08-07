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
from typing import TYPE_CHECKING

import numpy as np
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QTextBrowser

from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import (
    chemical_system_summary,
    trajectory_summary,
)

if TYPE_CHECKING:
    from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem


class TrajectoryInfo(QTextBrowser):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        self._header = kwargs.pop("header", "")
        self._footer = kwargs.pop("footer", "")
        super().__init__(*args, **kwargs)
        self.setOpenExternalLinks(True)

    @Slot(object)
    def update_panel(self, data: tuple):
        fullpath, incoming = data
        if incoming is None:
            self.clear()
            self.setHtml(fullpath)
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
            self.clear()
            return
        try:
            cs = incoming.chemical_system
        except AttributeError:
            LOG.error("Trajectory %s has no chemical system", incoming)
        else:
            text += self.summarise_chemical_system(cs)
        filtered = self.filter(text)
        self.setHtml(filtered)

    def summarise_chemical_system(self, cs: ChemicalSystem):
        return chemical_system_summary(cs)

    def filter(self, some_text: str, line_break="<br />"):
        new_text = ""
        if self._header:
            new_text += self._header + line_break
        if some_text is not None:
            new_text += line_break.join([x.strip() for x in some_text.split("\n")])
        if self._footer:
            new_text += line_break + self._footer
        return new_text
