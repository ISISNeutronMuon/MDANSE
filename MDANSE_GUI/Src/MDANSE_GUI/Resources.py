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
from qtpy.QtCore import QDir, QSize
from qtpy.QtGui import QIcon, QImage, QPixmap

from MDANSE.MLogging import LOG


def qimage_to_array(image: QImage) -> np.ndarray:
    image.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = image.width(), image.height()
    temp = image.bits()
    temp.setsize(w * h * 4)
    return np.frombuffer(temp, np.uint8).reshape((h, w, 4))


def mean_rgb(image_array: np.ndarray) -> float:
    luminance = (
        0.3 * image_array[:, :, 0]
        + 0.59 * image_array[:, :, 1]
        + 0.11 * image_array[:, :, 2]
    )
    luminance *= image_array[:, :, 3]
    return np.mean(luminance)


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
        LOG.info(f"Resources are in {res_dir.absolutePath()}")
        # res_dir.addSearchPath('icons', 'Src/PyQtGUI/Icons/')
        res_dir.setNameFilters(["*.png"])
        files = res_dir.entryList()
        for f in files:
            label = ".".join(str(f).split(".")[:-1])
            self._icons[label] = QIcon(res_dir.filePath(f))
            # print(f"Loaded {f} from {res_dir}")
        for (
            iname,
            icon,
        ) in self._icons.items():
            pixmap = icon.pixmap(QSize(64, 64))
            original_image: QImage = pixmap.toImage()
            inverted_image: QImage = pixmap.toImage()
            inverted_image.invertPixels()
            newpixmap = QPixmap.fromImage(inverted_image)
            value_orig = mean_rgb(qimage_to_array(original_image))
            value_inv = mean_rgb(qimage_to_array(inverted_image))
            if value_orig < value_inv:
                self._inverted_icons[iname] = QIcon(newpixmap)
            else:
                self._inverted_icons[iname] = QIcon(pixmap)
                self._icons[iname] = QIcon(newpixmap)
