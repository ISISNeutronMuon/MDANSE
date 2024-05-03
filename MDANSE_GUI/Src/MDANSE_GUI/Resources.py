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

from qtpy.QtCore import QDir, QSize
from qtpy.QtGui import QIcon, QPixmap


class Resources:
    def __init__(self):
        self._icons = {}
        self._inverted_icons = {}
        self.load_icons()

    def load_icons(self):
        from importlib.resources import files

        temp = files("MDANSE_GUI")
        # print(f"I got {temp} from the importlib.resources")
        res_dir = QDir(str(temp.joinpath("Icons")))
        print(f"Resources are in {res_dir.absolutePath()}")
        # res_dir.addSearchPath('icons', 'Src/PyQtGUI/Icons/')
        res_dir.setNameFilters(["*.png", "*.ico"])
        files = res_dir.entryList()
        for f in files:
            label = ".".join(str(f).split(".")[:-1])
            self._icons[label] = QIcon(res_dir.filePath(f))
            # print(f"Loaded {f} from {res_dir}")
        for (
            iname,
            icon,
        ) in self._icons.items():
            pixmap = icon.pixmap(QSize(32, 32))
            image = pixmap.toImage()
            image.invertPixels()
            newpixmap = QPixmap.fromImage(image)
            self._inverted_icons[iname] = QIcon(newpixmap)
