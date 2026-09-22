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

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from qtpy.QtCore import QEvent, Qt
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QApplication


class MDANSEMatPlotLibNavBar(NavigationToolbar2QT):
    def __init__(self, canvas, parent=None, coordinates=True):
        super().__init__(canvas, parent, coordinates)
        colour_scheme = QApplication.styleHints().colorScheme()
        self.icons_dark = []
        self.icons_light = []
        for action in self._actions.values():
            prev_icon = action.icon()
            pixmap = prev_icon.pixmap(24, 24)
            img = pixmap.toImage()
            img.invertPixels()
            new_icon = QIcon(QPixmap.fromImage(img))
            if colour_scheme == Qt.ColorScheme.Dark:
                dark_icon, light_icon = prev_icon, new_icon
            else:
                light_icon, dark_icon = prev_icon, new_icon
            self.icons_dark.append(dark_icon)
            self.icons_light.append(light_icon)

    def changeEvent(self, event):
        if event.type() == QEvent.PaletteChange:
            colour_scheme = QApplication.styleHints().colorScheme()
            for i, action in enumerate(self._actions.values()):
                if colour_scheme == Qt.ColorScheme.Dark:
                    action.setIcon(self.icons_dark[i])
                else:
                    action.setIcon(self.icons_light[i])
        super().changeEvent(event)
