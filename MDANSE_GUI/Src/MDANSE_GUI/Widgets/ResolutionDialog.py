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

from typing import List
import math

import numpy as np

from qtpy.QtWidgets import (
    QDialog,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QApplication,
)
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QDoubleValidator

import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)

from MDANSE.Framework.Units import measure
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)


widget_text_map = {
    "ideal": "ideal",
    "Gaussian": "gaussian",
    "Lorentzian": "lorentzian",
    "triangular": "triangular",
    "square": "square",
    "pseudo-Voigt": "pseudovoigt",
}


gauss_denum = 2.0 * (2.0 * math.log(2.0)) ** 0.5


def convert_parameters(fwhm: float, centre: float, peak_type: str) -> List[float]:
    """Takes the values from the ResolutionDialog as input,
    and returns the sigma and mu values as expected by MDANSE.
    The conversion between sigma and FWHM is different for
    different peak functions.

    Parameters
    ----------
    fwhm : float
        The FWHM of the peak, in rad/ps
    centre : float
        The centre of the peak, in rad/ps
    peak_type : str
        Name of the function, one of the values of the widget_text_map dict

    Returns
    -------
    List[float]
        A pair of [sigma, mu] values, or empty for ideal
    """
    if peak_type == "ideal":
        return []
    elif peak_type == "triangular":
        vals = [fwhm, centre]
    elif peak_type == "square":
        vals = [fwhm / 2, centre]
    elif peak_type == "gaussian":
        vals = [fwhm / gauss_denum, centre]
    elif peak_type == "lorentzian":
        vals = [fwhm / 2, centre]
    else:
        vals = [fwhm, centre]
    return vals[0], vals[1]


def revert_parameters(values: dict, peak_type: str) -> List[float]:
    """Converts the sigma and mu values back to FWHM and peak centre.
    Used for passing the values from the main GUI back to the
    helper dialog.

    Parameters
    ----------
    values : dict
        A dictionary of all the peak parameters from the InstrumentResolutionWidget
    peak_type : str
        Name of the function, one of the values of the widget_text_map dict

    Returns
    -------
    List[float]
        A pair of [FWHM, centre] values
    """
    if peak_type == "ideal":
        return [1.0, 0]
    elif peak_type == "triangular":
        vals = [values["sigma"], values["mu"]]
    elif peak_type == "square":
        vals = [values["sigma"] * 2, values["mu"]]
    elif peak_type == "gaussian":
        vals = [values["sigma"] * gauss_denum, values["mu"]]
    elif peak_type == "lorentzian":
        vals = [values["sigma"] * 2, values["mu"]]
    elif "oigt" in peak_type:
        try:
            sigma = (
                values["sigma_gaussian"] * gauss_denum + values["sigma_lorentzian"] * 2
            )
        except KeyError:
            sigma = 2.0
        try:
            mu = values["mu_gaussian"] + values["mu_lorentzian"]
        except KeyError:
            mu = 0.0
        vals = [sigma / 2, mu / 2]
    else:
        vals = [values["sigma"], values["mu"]]
    return vals[0], vals[1]


class ResolutionDialog(QDialog):

    parameters_changed = Signal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QGridLayout(self)
        self.setWindowTitle("Resolution Helper for MDANSE")
        self._resolution = None
        self.setLayout(layout)
        self._peak_selector = QComboBox(self)
        self._peak_selector.addItems(widget_text_map.keys())
        self._unit_selector = QComboBox(self)
        self._unit_selector.addItems(["meV", "1/cm", "THz"])
        self._fwhm = QLineEdit("1.0", self)
        self._centre = QLineEdit("0.0", self)
        self._eta = QLineEdit("0.0", self)
        self._eta.setEnabled(False)
        for ledit in [self._fwhm, self._centre, self._eta]:
            ledit.setValidator(QDoubleValidator(ledit))
            ledit.setPlaceholderText("N/A")
        self._omega_axis = np.linspace(-1.0, 1.0, 500)
        self._output_field = QTextEdit(self)
        self._output_field.setReadOnly(True)
        self._apply_button = QPushButton("Apply", self)
        self._apply_button.clicked.connect(self.apply_changes)
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
        layout.addWidget(self._output_field, number + 1, 0, 1, 2)
        layout.addWidget(self._apply_button, number + 2, 0)
        canvas = self.make_canvas()
        layout.addWidget(canvas, 0, 2, 8, 1)
        for widget in [self._fwhm, self._centre, self._eta]:
            widget.textChanged.connect(self.recalculate_peak)
        self._peak_selector.currentTextChanged.connect(self.update_model)
        self._unit_selector.currentTextChanged.connect(self.recalculate_peak)
        self.update_model(self._peak_selector.currentText())

    def make_canvas(self, width=12.0, height=9.0, dpi=100):
        """Creates a matplotlib figure for plotting

        Parameters
        ----------
        width : float, optional
            Figure width in inches, by default 12.0
        height : float, optional
            Figure height in inches, by default 9.0
        dpi : int, optional
            Figure resolution in dots per inch, by default 100

        Returns
        -------
        QWidget
            a widget containing both the figure and a toolbar below
        """
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
        """Activated on new value in the peak type combo box,
        creates the new IInstrumentResolution subclass.

        Parameters
        ----------
        new_model : str
            Name of the resolution class to create.
        """
        self._resolution_name = new_model
        self._resolution = IInstrumentResolution.create(widget_text_map[new_model])
        self._resolution.build_configuration()
        if "oigt" in new_model:
            for field in [self._fwhm, self._centre, self._eta]:
                field.setEnabled(True)
        elif "deal" in new_model:
            for field in [self._fwhm, self._centre, self._eta]:
                field.setEnabled(False)
        else:
            for field in [self._fwhm, self._centre]:
                field.setEnabled(True)
            self._eta.setEnabled(False)
        self.recalculate_peak()

    @Slot()
    def recalculate_peak(self):
        """The main method of the dialog.
        Collects the inputs from text fields and
        calculates the peak function on an array
        of points around the peak centre.
        """
        try:
            fwhm = abs(float(self._fwhm.text()))
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
            temp_name = widget_text_map[self._resolution_name]
            try:
                sigma, mu = convert_parameters(fwhm, centre, temp_name)
            except ValueError:
                self._fwhm_value = 0.0
            else:
                self.set_peak_parameter(mu * factor, "mu")
                self.set_peak_parameter(sigma * factor, "sigma")
        extra_width = abs(fwhm)
        if extra_width <= 1e-14:
            extra_width = 1
        self._omega_axis = np.linspace(
            factor * (centre - 3 * extra_width),
            factor * (centre + 3 * extra_width),
            501,  # odd number is needed for 'ideal' function to work
        )
        try:
            self._resolution.set_kernel(self._omega_axis, 1.0)
        except:
            self.update_text_output(error=True)
            self._apply_button.setEnabled(False)
        else:
            self._apply_button.setEnabled(True)
            self.update_text_output()
            self.update_plot()

    def update_fields(self, widget_values):
        """Method for passing the values from the main
        GUI into the helper dialog. Converts all the
        numbers from MDANSE inputs (sigma in rad/ps)
        to the ResolutionDialog values (FWHM in users's preferred units).
        During the execution of this method the signals
        of the widgets are blocked, not to trigger
        the sending of the input values which would
        overwrite the GUI values.

        Parameters
        ----------
        widget_values : tuple[str, dict]
            Widget values from InstrumentResolutionWidget
        """
        self.blockSignals(True)
        new_function_name = widget_values[0]
        offical_name = "missing"
        for key, value in widget_text_map.items():
            if new_function_name == value:
                offical_name = key
        new_params = widget_values[1]
        new_eta = new_params.get("eta", "0.0")
        try:
            fwhm, centre = revert_parameters(new_params, new_function_name)
        except:
            self.blockSignals(False)
            return
        self._peak_selector.setCurrentText(offical_name)
        if abs(fwhm) < 1e-12:
            new_fwhm = 0.0
        else:
            temp_value = fwhm / self._factor_value
            new_fwhm = round(
                temp_value,
                abs(math.floor(math.log10(abs(temp_value)))) + 3,
            )
        if abs(centre) < 1e-12:
            new_centre = 0.0
        else:
            temp_value = centre / self._factor_value
            new_centre = round(
                temp_value,
                abs(math.floor(math.log10(abs(temp_value)))) + 3,
            )
        self._fwhm.setText(str(new_fwhm))
        self._centre.setText(str(new_centre))
        self._eta.setText(str(new_eta))
        self.blockSignals(False)
        self.recalculate_peak()

    def set_peak_parameter(self, value: float, key: str):
        """A convenience method for passing an input value
        to the IInstrumentResolution class instance.

        Parameters
        ----------
        value : float
            numerical value of the peak parameter
        key : str
            name of the parameter from the 'settings' dictionary
        """
        self._resolution._configuration[key].configure(value)

    def update_text_output(self, rounding_precision=3, error=False):
        """Updates the text in the QTextEdit widget.
        It shows the user what MDANSE values will be
        created out of the current inputs.
        Rounding is applied to the numbers for legibility.

        Parameters
        ----------
        rounding_precision : int, optional
            number of significant places to include, by default 3
        """
        if error:
            text = "Current parameters do not produce a valid peak function.\n"
            text += "If your FWHM=0, you may need to change it."
            self._output_field.setText(text)
            return
        text = "Parameters in MDANSE internal units\n"
        results = {"function": self._resolution_name}
        for key, value in self._resolution._configuration.items():
            original_value = value["value"]
            if abs(original_value) < 1e-12:
                rounded_value = 0.0
            else:
                rounded_value = round(
                    original_value,
                    abs(math.floor(math.log10(abs(original_value))))
                    + rounding_precision,
                )
            text += f"settings[{key}] = {rounded_value}\n"
            results[key] = rounded_value
        self._output_field.setText(text)
        self._results = results

    def apply_changes(self):
        self.parameters_changed.emit(self._results)

    def update_plot(self):
        """Plots the latest peak function in the
        matplotlib figure.
        The plot has two x axes: one in user's units,
        and the other in MDANSE units.
        A dashed line indicates the full width at
        half maximum of the peak.
        """
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
        if not "deal" in self._resolution_name:
            axes.plot(xs * self._factor_value, ys, "r:")
        axes.grid(True)
        scale = self._factor_value
        second_axis = axes.secondary_xaxis(
            "top", functions=(lambda x: x / scale, lambda x: x / scale)
        )
        axes.set_xlabel("Energy [rad/ps]")
        second_axis.set_xlabel(f"Energy [{self._unit_value}]")
        self._figure.canvas.draw()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = ResolutionDialog()
    root.show()
    app.exec()
