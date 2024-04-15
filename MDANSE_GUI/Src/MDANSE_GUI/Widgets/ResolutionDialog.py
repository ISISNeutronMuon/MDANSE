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

from typing import Union, Iterable, Optional, List
from collections import OrderedDict
import math

from icecream import ic
import numpy as np

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

from MDANSE.Framework.Units import measure
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)
from MDANSE_GUI.InputWidgets.InstrumentResolutionWidget import widget_text_map


gauss_denum = 2.0 * (2.0 * math.log(2.0)) ** 0.5


def convert_parameters(fwhm: float, centre: float, peak_type: str) -> List[float]:
    if peak_type == "ideal":
        return []
    elif peak_type == "triangular":
        return [fwhm, centre]
    elif peak_type == "square":
        return [fwhm, centre]
    elif peak_type == "gaussian":
        return [fwhm / gauss_denum, centre]
    elif peak_type == "lorentzian":
        return [fwhm / 2, centre]
    else:
        return [fwhm, centre]


class ResolutionDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QGridLayout(self)
        self._resolution = None
        self.setLayout(layout)
        self._peak_selector = QComboBox(self)
        self._peak_selector.addItems(widget_text_map.keys())
        self._unit_selector = QComboBox(self)
        self._unit_selector.addItems(["meV", "1/cm", "THz"])
        self._fwhm = QLineEdit("1.0", self)
        self._centre = QLineEdit("0.0", self)
        self._eta = QLineEdit("N/A", self)
        self._eta.setEnabled(False)
        self._omega_axis = np.linspace(-1.0, 1.0, 500)
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
        layout.addWidget(canvas, 0, 2, 7, 1)
        for widget in [self._fwhm, self._centre, self._eta]:
            widget.textChanged.connect(self.recalculate_peak)
        self._peak_selector.currentTextChanged.connect(self.update_model)
        self._unit_selector.currentTextChanged.connect(self.recalculate_peak)
        self.update_model(self._peak_selector.currentText())

    def make_canvas(self, width=12.0, height=9.0, dpi=150):
        canvas = QWidget(self)
        layout = QVBoxLayout(canvas)
        figure = mpl.figure(figsize=[width, height], dpi=dpi, frameon=True)
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
        ic()
        self._resolution_name = new_model
        self._resolution = IInstrumentResolution.create(widget_text_map[new_model])
        self._resolution.build_configuration()
        if "oigt" in new_model:
            self._eta.setEnabled(True)
            self._eta.setText("0.0")
        else:
            self._eta.setEnabled(False)
            self._eta.setText("N/A")
        self.recalculate_peak()

    @Slot()
    def recalculate_peak(self):
        ic()
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
        factor = measure(1.0, iunit=unit, equivalent=True).toval("rad/ps")
        self._factor_value = factor
        self._fwhm_value = fwhm
        self._centre_value = centre
        self._unit_value = unit
        if "oigt" in self._resolution_name:
            gauss_sigma, gauss_mu = convert_parameters(fwhm, centre, "gaussian")
            lorentz_sigma, lorentz_mu = convert_parameters(fwhm, centre, "lorentzian")
            self.set_peak_parameter(lorentz_mu * factor, "mu_lorentzian")
            self.set_peak_parameter(gauss_mu * factor, "mu_gaussian")
            self.set_peak_parameter(lorentz_sigma * factor, "sigma_lorentzian")
            self.set_peak_parameter(gauss_sigma * factor, "sigma_gaussian")
            self.set_peak_parameter(eta, "eta")
        else:
            try:
                sigma, mu = convert_parameters(fwhm, centre, self._resolution_name)
            except ValueError:
                print(f"Failed to convert parameters for {self._resolution_name}")
                self._fwhm_value = 0.0
            else:
                self.set_peak_parameter(mu * factor, "mu")
                self.set_peak_parameter(sigma * factor, "sigma")
        self._omega_axis = np.linspace(-3 * factor * fwhm, 3 * factor * fwhm, 500)
        self._resolution.set_kernel(self._omega_axis, 1.0)
        self.update_plot()

    def set_peak_parameter(self, value: float, key: str):
        self._resolution._configuration[key].configure(value)

    def update_plot(self):
        ic()
        self._figure.clear()
        axes = self._figure.add_axes(111)
        axes.plot(self._omega_axis, self._resolution._omegaWindow)
        hh = np.max(self._resolution._omegaWindow) / 2
        xs = (
            np.array(
                [
                    -self._fwhm_value / 2,
                    -self._fwhm_value / 2,
                    self._fwhm_value / 2,
                    self._fwhm_value / 2,
                ]
            )
            + self._centre_value
        )
        ys = np.array([0.0, hh, hh, 0.0])
        axes.plot(xs * self._factor_value, ys, "r:")
        axes.grid(True)
        axes.set_xlabel(f"Energy [{self._unit_value}]")
        scale = self._factor_value
        second_axis = axes.secondary_xaxis(
            "top", functions=(lambda x: x * scale, lambda x: x * scale)
        )
        second_axis.set_xlabel("Energy [rad/ps]")
        self._figure.canvas.draw()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = ResolutionDialog()
    root.show()
    app.exec()
