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

import MDAnalysis as mda
from qtpy.QtWidgets import QComboBox, QLineEdit, QPushButton

from .InputFileWidget import InputFileWidget


class MDAnalysisTopologyFileWidget(InputFileWidget):
    def __init__(self, *args, format_options=sorted(mda._PARSERS.keys()), **kwargs):
        self.format_options = ["AUTO"] + list(format_options)
        super().__init__(*args, **kwargs)

    def add_widgets_to_layout(self):
        field = QLineEdit(self._base)
        self._field = field
        field.setText(str(self._default_value))
        field.setPlaceholderText(str(self._default_value))
        field.setToolTip(self._tooltip_text)
        self._layout.addWidget(field)

        self.format_combo = QComboBox(self._base)
        self.format_combo.addItems(self.format_options)
        self._layout.addWidget(self.format_combo)

        button = QPushButton("Browse", self._base)
        self._layout.addWidget(button)

        field.textChanged.connect(self.updateValue)
        self.format_combo.currentTextChanged.connect(self.updateValue)
        button.clicked.connect(self.valueFromDialog)

    def get_widget_value(self) -> tuple[str, str]:
        """
        Returns
        -------
        tuple
            A tuple of the topology file path and format.
        """
        strval = super().get_widget_value()
        format = self.format_combo.currentText()
        return strval, format
