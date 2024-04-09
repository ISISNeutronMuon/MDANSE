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

from typing import Union, Iterable, Optional
from collections import OrderedDict
import copy

from icecream import ic

from qtpy.QtWidgets import (
    QDialog,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QComboBox,
    QMenu,
    QLineEdit,
    QTableView,
    QFormLayout,
    QHBoxLayout,
    QCheckBox,
    QTextEdit,
    QApplication,
)
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel, QObject
from qtpy.QtGui import (
    QFont,
    QEnterEvent,
    QStandardItem,
    QStandardItemModel,
    QIntValidator,
    QDoubleValidator,
    QValidator,
)

import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)

from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)
from MDANSE_GUI.InputWidgets.InstrumentResolutionWidget import widget_text_map


class ResolutionDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QGridLayout(self)
        self._resolution = None
        self.setLayout(layout)
        self._peak_selector = QComboBox(self)
        self._peak_selector.addItems(widget_text_map.keys())
        self._unit_selector = QComboBox(self)
        self._unit_selector.addItems(["meV", "cm-1", "THz"])
        self._fwhm = QLineEdit("1.0", self)
        self._centre = QLineEdit("0.0", self)
        self._eta = QLineEdit("N/A", self)
        self._eta.setEnabled(False)
        text_labels = ["Peak function", "Energy unit", "FWHM", "Centre", "eta"]
        for number, widget in enumerate(
            [
                self._peak_selector,
                self._unit_selector,
                self._fwhm,
                self._centre,
                self._eta,
            ]
        ):
            layout.addWidget(QLabel(text_labels[number], self), number, 0)
            layout.addWidget(widget, number, 1)
        canvas = self.make_canvas()
        layout.addWidget(canvas, 0, 2, 5, 1)
        for widget in [self._fwhm, self._centre, self._eta]:
            widget.textChanged.connect(self.update_plot)
        self._peak_selector.currentTextChanged.connect(self.update_model)

    def make_canvas(self, width=8.0, height=6.0, dpi=300):
        canvas = QWidget(self)
        layout = QVBoxLayout(canvas)
        figure = mpl.figure(figsize=[width, height], dpi=dpi)  # , frameon = False)
        figAgg = FigureCanvasQTAgg(figure)
        figAgg.setParent(canvas)
        figAgg.updateGeometry()
        toolbar = NavigationToolbar2QTAgg(figAgg, canvas)
        toolbar.update()
        layout.addWidget(figAgg)
        layout.addWidget(toolbar)
        self._figure = figure
        return canvas

    @Slot(str)
    def update_model(self, new_model: str):
        self._resolution_name = new_model
        self._resolution = IInstrumentResolution.create(widget_text_map[new_model])
        if "oigt" in new_model:
            self._eta.setEnabled(True)
            self._eta.setText("0.0")
        else:
            self._eta.setEnabled(False)
            self._eta.setText("N/A")

    @Slot()
    def update_plot(self):
        try:
            fwhm = float(self._fwhm.text())
        except:
            return
        try:
            centre = float(self._centre.text())
        except:
            return
        if "oigt" in self._resolution_name:
            try:
                eta = float(self._eta.text())
            except:
                return
        unit = self._unit_selector.currentText()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = ResolutionDialog()
    root.show()
    app.exec()
