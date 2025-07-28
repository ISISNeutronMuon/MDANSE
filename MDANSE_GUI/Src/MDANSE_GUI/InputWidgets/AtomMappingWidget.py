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

import json
from collections import defaultdict

from qtpy.QtCore import Slot
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.AtomMapping import guess_element
from MDANSE_GUI.InputWidgets.InputFileWidget import InputFileWidget
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class AtomMappingHelperDialog(QDialog):
    """The atom mapping helper dialog used to help generate the atom
    map setting JSON string.
    """

    def __init__(
        self, field_widget: InputFileWidget, field: QLineEdit, parent, *args, **kwargs
    ):
        """
        Parameters
        ----------
        field_widget: InputFileWidget
            The input file widget which is used to obtain the group and
            atom labels.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        """
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle("Atom mapping helper")
        self.min_width = kwargs.get("min_width", 500)
        self.min_height = kwargs.get("min_width", 600)
        self.resize(self.min_width, self.min_height)
        self.setMinimumWidth(self.min_width)
        self.setMinimumHeight(self.min_height)
        self._field = field

        self._file_widget = field_widget

        self.layout = QVBoxLayout()
        buffer_0 = QWidget(self)
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Group"))
        header_layout.addWidget(QLabel("Atom Label"))
        header_layout.addWidget(QLabel("Element"))
        buffer_0.setLayout(header_layout)

        self.mapping_widgets = []
        buffer_1 = QWidget(self)
        scroll_area = QScrollArea()
        scroll_area.setWidget(buffer_1)
        scroll_area.setWidgetResizable(True)
        self.mapping_layout = QGridLayout()
        buffer_1.setLayout(self.mapping_layout)

        button_layout = QHBoxLayout()
        apply = QPushButton("Apply")
        auto = QPushButton("Auto Fill")
        close = QPushButton("Close")
        apply.clicked.connect(self.apply)
        auto.clicked.connect(self.auto_fill)
        close.clicked.connect(self.close)
        button_layout.addWidget(apply)
        button_layout.addWidget(auto)
        button_layout.addWidget(close)

        self.layout.addWidget(buffer_0)
        self.layout.addWidget(scroll_area)
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.all_symbols = ATOMS_DATABASE.atoms
        self.labels = None

    def update_helper(self) -> None:
        """Get the atoms labels from the file widget and add mapping
        widgets to the helper.
        """
        self.clear_panel()
        if not self._file_widget._configurator.valid:
            return

        self.labels = self._file_widget._configurator.labels
        for i, label in enumerate(self.labels):
            w0 = QLabel(label.grp_label.replace(";", "\n"))
            w1 = QLabel(label.atm_label)
            w2 = QComboBox()
            # this combobox can be slow without this policy since we
            # are adding alot of items
            w2.setSizeAdjustPolicy(w2.AdjustToMinimumContentsLengthWithIcon)
            w2.addItems(self.all_symbols)
            self.mapping_widgets.append((w0, w1, w2))
            self.mapping_layout.addWidget(w0, i, 0)
            self.mapping_layout.addWidget(w1, i, 1)
            self.mapping_layout.addWidget(w2, i, 2)

        self.auto_fill()

    def clear_panel(self) -> None:
        """Clear the widgets so that it leaves an empty mapping
        layout.
        """
        for ws in self.mapping_widgets:
            for w in ws:
                w.setParent(None)
                self.mapping_layout.removeWidget(w)
        self.mapping_widgets = []

    def auto_fill(self) -> None:
        """Autofill the comboboxes using a simple guess."""
        for i, (_, w1, w2) in enumerate(self.mapping_widgets):
            try:
                label = self.labels[i]
                guess = guess_element(label.atm_label, mass=label.mass)
                idx = self.all_symbols.index(guess)
                w2.setCurrentIndex(idx)
            except AttributeError:
                w2.setCurrentIndex(-1)

    def apply(self) -> None:
        """Convert the selection in the mapping widgets to a JSON string
        and set the field.
        """
        settings = defaultdict(lambda: dict())
        for w0, w1, w2 in self.mapping_widgets:
            settings[w0.text().replace("\n", ";")][w1.text()] = w2.currentText()
        self._field.setText(json.dumps(settings))


class AtomMappingWidget(WidgetBase):
    """The atom mapping widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_value = "{}"
        self._value = default_value
        self._field = QLineEdit(default_value, self._base)
        self._field.setPlaceholderText(default_value)
        self._field.setMaxLength(2147483647)  # set to the largest possible
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "Replace the chemical elements in the system. The order of symbols is <current>:<new>"
        self._field.setToolTip(tooltip_text)

        # file input widgets should be loaded into the _widgets list
        # before this one
        for widget in self.parent()._widgets:
            if (
                widget._configurator
                is self._configurator.configurable[
                    self._configurator.dependencies["input_file"]
                ]
            ):
                self._file_widget = widget
                break

        self.helper = AtomMappingHelperDialog(
            self._file_widget, self._field, self._base
        )
        self.helper_button = QPushButton("Atom mapping helper", self._base)
        self.helper_button.clicked.connect(self.helper_dialog)
        self.helper_button.setEnabled(False)
        self._field.textChanged.connect(self.updateValue)
        self._default_value = default_value
        self._layout.addWidget(self._field)
        self._layout.addWidget(self.helper_button)
        self._file_widget.value_changed.connect(self.update_helper_button)
        self.update_labels()
        self.updateValue()

    @Slot()
    def update_helper_button(self) -> None:
        """Enables the helper button when the file widget has a valid
        file input.
        """
        if self._file_widget._configurator.valid:
            self.helper_button.setEnabled(True)
            self.helper.update_helper()
            self.helper.apply()
        else:
            self.helper_button.setEnabled(False)
            self.helper.close()
            self.helper.clear_panel()
            self.helper.apply()

    @Slot()
    def helper_dialog(self) -> None:
        """Opens the helper dialog."""
        if self.helper.isVisible():
            geometry = self.helper.saveGeometry()
            self.helper.previous_geometry = geometry
            self.helper.close()
        else:
            if hasattr(self.helper, "previous_geometry"):
                self.helper.restoreGeometry(self.helper.previous_geometry)
            self.helper.show()

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON string map setting.
        """
        mapping_string = self._field.text()
        if len(mapping_string) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return mapping_string
