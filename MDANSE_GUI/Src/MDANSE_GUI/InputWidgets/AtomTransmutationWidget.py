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
from qtpy.QtCore import Qt, QEvent, Slot, QObject
from qtpy.QtGui import QStandardItem
from qtpy.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QDialog,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QTextEdit,
)

from MDANSE.Framework.AtomTransmutation import AtomTransmuter
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import AtomSelectionWidget
from MDANSE_GUI.InputWidgets.AtomSelectionWidget import HelperDialog


class TransmutationHelper(HelperDialog):

    def __init__(self, transmuter: AtomTransmuter, field: QLineEdit, parent, *args,
                 **kwargs):
        self.transmuter = transmuter
        self.transmutation_textbox = QTextEdit()
        self.transmutation_textbox.setReadOnly(True)
        super().__init__(transmuter.selector, field, parent, min_width=700, *args, **kwargs)

    def create_layouts(self):
        layouts = super().create_layouts()
        right = QVBoxLayout()
        right.addWidget(self.transmutation_textbox)
        return layouts + [right]

    def left_widgets(self):
        widgets = super().left_widgets()
        transmutation = QGroupBox("transmutation")
        transmutation_layout = QVBoxLayout()

        combo_layout = QHBoxLayout()
        combo = QComboBox()
        combo.addItems(ATOMS_DATABASE.atoms)
        label = QLabel("Transmute selection to:")

        combo_layout.addWidget(label)
        combo_layout.addWidget(combo)
        transmutation_layout.addLayout(combo_layout)

        transmute = QPushButton("Transmute")
        transmutation_layout.addWidget(transmute)

        transmutation.setLayout(transmutation_layout)
        return widgets + [transmutation]


class AtomTransmutationWidget(AtomSelectionWidget):
    """The atoms transmutation widget."""
    push_button_text = "Atom transmutation helper"
    default_value = "{}"
    tooltip_text = "Specify the atom transmutation that will be used in the analysis. The input is a JSON string, and can be created using the helper dialog."

    def create_helper(self) -> HelperDialog:
        transmuter = self._configurator.get_transmuter()
        return TransmutationHelper(transmuter, self._field, self._base)
