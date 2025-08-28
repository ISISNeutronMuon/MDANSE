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

import matplotlib.pyplot as mpl
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG

widget_text_map = {
    "ideal": "ideal",
    "Gaussian": "gaussian",
    "Lorentzian": "lorentzian",
    "triangular": "triangular",
    "square": "square",
    "pseudo-Voigt": "pseudovoigt",
}


gauss_denum = 2.0 * (2.0 * math.log(2.0)) ** 0.5


def convert_parameters(
    fwhm: float, centre: float, peak_type: str
) -> tuple[float, float]:
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
    sigma
        Std. dev. of resolution.
    mu
        Mean of resolution.
    """
    if peak_type == "ideal":
        fwhm, centre = 0.0, 0.0
    elif peak_type == "triangular":
        pass
    elif peak_type == "square":
        fwhm = fwhm / 2
    elif peak_type == "gaussian":
        fwhm = fwhm / gauss_denum
    elif peak_type == "lorentzian":
        fwhm = fwhm / 2

    return fwhm, centre


def revert_parameters(values: dict, peak_type: str) -> tuple[float, float]:
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
    FWHM
        Resolution full width half maximum.
    Centre
        Peak centre.
    """
    if peak_type == "ideal":
        sigma, mu = 1.0, 0.0
    elif peak_type == "triangular":
        sigma, mu = values["sigma"], values["mu"]
    elif peak_type == "square":
        sigma, mu = values["sigma"] * 2, values["mu"]
    elif peak_type == "gaussian":
        sigma, mu = values["sigma"] * gauss_denum, values["mu"]
    elif peak_type == "lorentzian":
        sigma, mu = values["sigma"] * 2, values["mu"]

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
        return sigma / 2, mu / 2
    else:
        sigma, mu = values["sigma"], values["mu"]

    return sigma, mu


class ResolutionCalculator:
    def __init__(self) -> None:
        self._valid = False
        self._fwhm_value = 1.0
        self._centre_value = 0.0
        self._unit_value = "meV"
        self._eta_value = 0.0

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
        self.recalculate_peak(
            self._fwhm_value, self._centre_value, self._eta_value, self._unit_value
        )

    def recalculate_peak(self, fwhm, centre, eta, unit):
        """The main method of the dialog.
        Collects the inputs from text fields and
        calculates the peak function on an array
        of points around the peak centre.
        """
        factor = measure(1.0, iunit=unit, equivalent=True).toval("rad/ps")
        self._factor_value = factor
        self._fwhm_value = float(fwhm)
        self._centre_value = float(centre)
        self._unit_value = unit
        try:
            self._eta_value = float(eta)
        except TypeError:
            self._eta_value = None
        if "oigt" in self._resolution_name:
            gauss_sigma, gauss_mu = convert_parameters(
                self._fwhm_value, self._centre_value, "gaussian"
            )
            lorentz_sigma, lorentz_mu = convert_parameters(
                self._fwhm_value, self._centre_value, "lorentzian"
            )
            self.set_peak_parameter(lorentz_mu * factor, "mu_lorentzian")
            self.set_peak_parameter(gauss_mu * factor, "mu_gaussian")
            self.set_peak_parameter(lorentz_sigma * factor, "sigma_lorentzian")
            self.set_peak_parameter(gauss_sigma * factor, "sigma_gaussian")
            self.set_peak_parameter(self._eta_value, "eta")
        else:
            temp_name = widget_text_map[self._resolution_name]
            try:
                sigma, mu = convert_parameters(
                    self._fwhm_value, self._centre_value, temp_name
                )
            except ValueError:
                self._fwhm_value = 0.0
            else:
                if "deal" not in self._resolution_name:
                    self.set_peak_parameter(mu * factor, "mu")
                    self.set_peak_parameter(sigma * factor, "sigma")
        extra_width = abs(self._fwhm_value)
        if extra_width <= 1e-14:
            extra_width = 1
        self._omega_axis = np.linspace(
            factor * (centre - 3 * extra_width),
            factor * (centre + 3 * extra_width),
            501,  # odd number is needed for 'ideal' function to work
        )
        try:
            self._resolution.set_kernel(self._omega_axis, 1.0)
        except Exception:
            self._valid = False
        else:
            self._valid = True

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
        try:
            self._resolution._configuration[key].configure(value)
        except KeyError:
            LOG.warning(f"Could not find {key} in {self._resolution._configuration}")

    def summarise_results(self, rounding_precision=3):
        results = {"function": self._resolution_name}
        text = ""
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
        return text, results


class ResolutionWidget(QWidget):
    parameters_changed = Signal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._calculator = ResolutionCalculator()

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
        self._calculator.update_model(new_model)
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
        except Exception:
            return
        try:
            centre = float(self._centre.text())
        except Exception:
            return
        if "oigt" in self._resolution_name:
            try:
                eta = float(self._eta.text())
            except Exception:
                return
        else:
            eta = None
        unit = self._unit_selector.currentText()
        self._calculator.recalculate_peak(fwhm, centre, eta, unit)
        if self._calculator._valid:
            self._apply_button.setEnabled(True)
            self.update_text_output()
            self.update_plot()
        else:
            self.update_text_output(error=True)
            self._apply_button.setEnabled(False)

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
        except Exception:
            self.blockSignals(False)
            return
        self._peak_selector.setCurrentText(offical_name)
        if abs(fwhm) < 1e-12:
            new_fwhm = 0.0
        else:
            temp_value = fwhm / self._calculator._factor_value
            new_fwhm = round(
                temp_value,
                abs(math.floor(math.log10(abs(temp_value)))) + 3,
            )
        if abs(centre) < 1e-12:
            new_centre = 0.0
        else:
            temp_value = centre / self._calculator._factor_value
            new_centre = round(
                temp_value,
                abs(math.floor(math.log10(abs(temp_value)))) + 3,
            )
        self._fwhm.setText(str(new_fwhm))
        self._centre.setText(str(new_centre))
        self._eta.setText(str(new_eta))
        self.blockSignals(False)
        self.recalculate_peak()

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
        temp_text, results = self._calculator.summarise_results(
            rounding_precision=rounding_precision
        )
        self._output_field.setText(text + temp_text)
        self._results = results

    @Slot()
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
        axes.plot(
            self._calculator._omega_axis, self._calculator._resolution._omegaWindow
        )
        hh = np.max(self._calculator._resolution._omegaWindow) / 2
        xs = (
            np.array(
                [
                    -self._calculator._fwhm_value / 2,
                    -self._calculator._fwhm_value / 2,
                    self._calculator._fwhm_value / 2,
                    self._calculator._fwhm_value / 2,
                ]
            )
            + self._calculator._centre_value
        )
        ys = np.array([0.0, hh, hh, 0.0])
        if "deal" not in self._resolution_name:
            axes.plot(xs * self._calculator._factor_value, ys, "r:")
        axes.grid(True)
        scale = self._calculator._factor_value
        second_axis = axes.secondary_xaxis(
            "top", functions=(lambda x: x / scale, lambda x: x / scale)
        )
        axes.set_xlabel("Energy [rad/ps]")
        second_axis.set_xlabel(f"Energy [{self._calculator._unit_value}]")
        self._figure.canvas.draw()
