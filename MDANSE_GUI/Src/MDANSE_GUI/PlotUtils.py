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
from qtpy.QtGui import QIcon, QPixmap


class MDANSEMatPlotLibNavBar(NavigationToolbar2QT):
    def changeEvent(self, event):
        if event.type() == event.PaletteChange:
            for action in self._actions.values():
                pixmap = action.icon().pixmap(24, 24)
                img = pixmap.toImage()
                img.invertPixels()
                new_pixmap = QPixmap.fromImage(img)
                action.setIcon(QIcon(new_pixmap))
        super().changeEvent(event)
