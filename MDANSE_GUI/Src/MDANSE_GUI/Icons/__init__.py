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

import os

from qtpy.QtCore import QDir
from qtpy.QtGui import QIcon


class PyQtIcons:
    def __init__(self, path):
        self.res_dir = QDir(path)
        self._icons = {}
        self.res_dir.setNameFilters(["*.png"])
        files = self.res_dir.entryList()
        for f in files:
            label = ".".join(str(f).split(".")[:-1])
            self._icons[label] = QIcon(self.res_dir.filePath(f))


ICONS = PyQtIcons(".")
