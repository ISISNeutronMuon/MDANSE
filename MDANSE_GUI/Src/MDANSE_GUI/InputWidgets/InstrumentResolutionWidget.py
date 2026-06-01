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

from itertools import count
from typing import TYPE_CHECKING

from more_itertools import padded
from qtpy.QtCore import Slot
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
)

from MDANSE.Framework.Parameters import InstrumentResolution
from MDANSE_GUI.InputWidgets.ComboWidget import ComboWidget
from MDANSE_GUI.InputWidgets.FloatWidget import FloatWidget
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Utils import block_signals
from MDANSE_GUI.Widgets.ResolutionDialog import ResolutionDialog
from MDANSE_GUI.Widgets.ResolutionWidget import WIDGET_TEXT_MAP


class InstrumentResolutionWidget(WidgetBase[InstrumentResolution]):
    def __init__(self, *args, layout_type: None = None, **kwargs):
        if layout_type is not None:
            raise ValueError("layout_type may not be non-None")

        super().__init__(*args, layout_type="QGridLayout", **kwargs)

        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The peak function used for smearing/smooting the results. Pick 'ideal' for no smearing."

        self._dialog_button = QPushButton("Helper Dialog", self._base)
        self._dialog_button.clicked.connect(self.helper_dialog)
        self._dialog_button.setEnabled(True)
        self.helper = ResolutionDialog(self._base)
        self.helper._panel.parameters_changed.connect(self.set_parameters_from_dialog)
        self._layout.addWidget(self._dialog_button, 0, 0)

        self._type_combo = ComboWidget(
            parent=self._base,
            base_type="QWidget",
            label="Kernel",
            tooltip=tooltip_text,
            configurable=self.parameter,
            choices=tuple(map(str.capitalize, WIDGET_TEXT_MAP.keys())),
            prop="kernel",
            parameter=self.parameter.descriptors["kernel"],
        )
        self.add_widget(self._type_combo, "kernel", add_to_layout=False)
        self._type_combo._field.currentTextChanged.connect(self.change_function)
        self._layout.addWidget(self._type_combo._base, 0, 1)

        self.change_function()
        self.updateValue()

    def set_value(self, value: tuple[str, dict]) -> None:
        self.change_function(*value)

    def set_field_values(self, new_params: dict) -> None:
        for key, val in new_params.items():
            self._widgets_in_layout[f"param_{key}"].setValue(val)

    @property
    def param_widgets(self) -> dict[str, FloatWidget]:
        return {
            key: val
            for key, val in self._raw_widgets.items()
            if key.startswith("param_")
        }

    @Slot()
    def change_function(
        self,
        new_kernel: str | None = None,
        new_parameters: dict[str, float] | None = None,
    ) -> None:
        if new_kernel is not None:
            self._type_combo._field.currentTextChanged.disconnect()
            self.parameter.kernel = new_kernel
            self._type_combo._field.setCurrentText(new_kernel)
            self._type_combo._field.currentTextChanged.connect(self.change_function)

        kernel = self.parameter.kernel

        for key in self.param_widgets:
            self.remove_widget(key)

        for i, key in enumerate(kernel.parameters):
            widget = FloatWidget(
                parent=self._base,
                base_type="QWidget",
                label=key,
                tooltip=f"Set the {key} parameter.",
                configurable=self.parameter.kernel,
                prop=key,
                parameter=self.parameter.kernel.descriptors[key],
            )
            self.add_widget(widget, f"param_{key}", add_to_layout=False)

            row, col = divmod(i, 2)
            self._layout.addWidget(widget._base, row + 1, col)

        if new_parameters:
            for key, val in new_parameters.items():
                self.param_widgets[f"param_{key}"]._field.setValue(val)

    def get_widget_value(self) -> dict[str, float]:
        function = type(self.parameter.kernel).__name__
        params = self.parameter.kernel.configuration
        self.helper._panel.update_fields((function, params))
        return params

    @Slot(dict)
    def set_parameters_from_dialog(self, inp: dict) -> None:
        peak_function = inp.pop("function", None)
        if peak_function is None:
            return

        self.change_function(new_kernel=peak_function, new_parameters=inp)

    @Slot()
    def helper_dialog(self) -> None:
        if self.helper.isVisible():
            geometry = self.helper.saveGeometry()
            self.helper.previous_geometry = geometry
            self.helper.close()
            return

        if hasattr(self.helper, "previous_geometry"):
            self.helper.restoreGeometry(self.helper.previous_geometry)
        self.helper.show()
