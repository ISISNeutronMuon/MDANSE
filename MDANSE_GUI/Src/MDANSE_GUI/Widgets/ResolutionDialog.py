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
from __future__ import annotations

import math

import numpy as np
from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import QApplication, QDialog, QVBoxLayout

from MDANSE_GUI.Widgets.ResolutionWidget import ResolutionWidget


class ResolutionDialog(QDialog):
    parameters_changed = Signal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setLayout(QVBoxLayout(self))
        self._panel = ResolutionWidget()
        self.layout().addWidget(self._panel)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = ResolutionDialog()
    root.show()
    app.exec()
