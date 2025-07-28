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

from typing import Any

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from MDANSE_GUI.Tabs.Plotters.Plotter import (
    NORMALISATION_DEFAULTS,
    enum_to_str,
    str_to_enum,
)

NORM_ERROR_STYLE = "QWidget { background-color:rgb(220,210,30); font-weight: bold }"
NORM_CLEAN_STYLE = "QWidget { }"


class NormalisationWidget(QWidget):
    """A set of inputs defining how to normalise data in the plot."""

    new_values = Signal(dict)

    def __init__(self, *args, **kwargs) -> None:
        """Create all the input widgets in a horizontal layout."""
        super().__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self._current_maxlength = 1
        self.combo_sum_average = QComboBox(self)
        self.minspin = QSpinBox(self)
        self.maxspin = QSpinBox(self)
        self.apply_norm = QCheckBox("Normalise data:", self)
        for widget in [
            self.apply_norm,
            QLabel("divide curves by"),
            self.combo_sum_average,
            QLabel("of points from"),
            self.minspin,
            QLabel("to"),
            self.maxspin,
            QLabel("(indices)"),
        ]:
            layout.addWidget(widget)
        self.apply_norm.setChecked(NORMALISATION_DEFAULTS["apply"])
        self.minspin.setValue(NORMALISATION_DEFAULTS["min_index"])
        self.maxspin.setValue(NORMALISATION_DEFAULTS["max_index"])
        self.combo_sum_average.addItems(["average", "sum"])
        self.combo_sum_average.setCurrentText(
            enum_to_str(NORMALISATION_DEFAULTS["operation"])
        )
        self.minspin.valueChanged.connect(self.collect_values)
        self.maxspin.valueChanged.connect(self.collect_values)
        self.minspin.valueChanged.connect(self.update_min_of_right_box)
        self.maxspin.valueChanged.connect(self.update_max_of_left_box)
        self.apply_norm.checkStateChanged.connect(self.collect_values)
        self.combo_sum_average.currentTextChanged.connect(self.collect_values)

    @Slot(int)
    def update_spinbox_limits(self, curve_length: int):
        """Update spinbox limits based on the current plot contents.

        Parameters
        ----------
        curve_length : int
            maximum data point index in the current plots

        """
        self._current_maxlength = curve_length
        newmax = abs(curve_length)
        for num, sb in enumerate([self.minspin, self.maxspin]):
            current_value = sb.value()
            sb.setMinimum(num)
            sb.setMaximum(newmax)
            new_value = min(current_value, newmax)
            new_value = max(new_value, num)
            sb.setValue(new_value)
            if num == 0:
                self.update_min_of_right_box(new_value)
            else:
                self.update_max_of_left_box(new_value)

    @Slot(int)
    def update_max_of_left_box(self, new_max: int):
        """Set the maximum value of the lower spin box.

        This is used to make sure that the lower limit of the range
        is really always lower that the upper limit.

        Parameters
        ----------
        new_max : int
            current value of the upper range limit
        """
        self.minspin.setMaximum(min(new_max - 1, self._current_maxlength))

    @Slot(int)
    def update_min_of_right_box(self, new_min: int):
        """Set the minimum value of the higher spin box.

        This is used to make sure that the upper range limit
        is really higher than the lower limit

        Parameters
        ----------
        new_min : int
            Current value of the lower range limit spin box
        """
        self.maxspin.setMinimum(max(new_min + 1, 0))

    @Slot()
    def collect_values(self) -> dict[str, Any]:
        """Collect an emit values from the input widgets.

        Returns
        -------
        dict[str, Any]
            values as in NORMALISATION_DEFAULTS

        """
        results = {
            "apply": self.apply_norm.isChecked(),
            "min_index": self.minspin.value(),
            "max_index": self.maxspin.value(),
            "operation": str_to_enum(self.combo_sum_average.currentText()),
        }
        self.new_values.emit(results)
        return results

    @Slot(str)
    def mark_error(self, error_text: str):
        """Change widget background colour and tooltip to indicate a problem.

        If the input parameters result in a scaling factor 0, the norm is not
        applied. The background colour change should indicate to the user
        that a problem has occurred with the normalisation, and the tooltip
        text will contain additional details.

        Parameters
        ----------
        error_text : str
            Collected normalisation error messages as a text string
        """
        self.setStyleSheet(NORM_ERROR_STYLE)
        self.setToolTip(error_text)

    @Slot()
    def clear_error(self):
        """Restores the normal appearance to the normalisation widgets."""
        self.setStyleSheet(NORM_CLEAN_STYLE)
        self.setToolTip("")
