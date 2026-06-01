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

from typing import TYPE_CHECKING

from MDANSE.Framework.Parameters import MolecularAxis
from MDANSE_GUI.InputWidgets.IntegerWidget import IntegerWidget
from MDANSE_GUI.InputWidgets.MoleculeWidget import MoleculeWidget
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Utils import block_signals


class MoleculeAndAxisWidget(WidgetBase[MolecularAxis]):
    """Widget for selecting a molecule type and an orientation vector.

    If the atom indices are not defined, the calculation will use
    the principal axis of the molecule determined from the moment
    of inertia.

    If one index is given, the molecule axis will be a vector from
    the molecule centre to the atom with the given index.

    If two indices are given, the molecule axis will be a vector
    between the atoms with the two indices.
    """

    def __init__(self, *args, **kwargs):
        """Populate the combo box with valid molecule names."""
        super().__init__(*args, **kwargs)

        # Force deps
        self.parameter.last_deps = self.parameter._get_deps(self._configurable)
        tooltip_text = "Hello"

        self.molecule = MoleculeWidget(
            parent=self._base,
            base_type="QWidget",
            label="Molecule",
            tooltip=tooltip_text,
            parent_widget=self,
            configurable=self.parameter,
            prop="molecule",
            parameter=self.parameter.descriptors["molecule"],
        )

        self.add_widget(self.molecule, key="molecule")

        self.axis_1 = IntegerWidget(
            parent=self._base,
            base_type="QWidget",
            label="Axis_1",
            tooltip=tooltip_text,
            parent_widget=self,
            configurable=self.parameter,
            prop="axis_1",
            parameter=self.parameter.descriptors["axis_1"],
        )

        self.add_widget(self.axis_1, key="axis_1")

        self.axis_2 = IntegerWidget(
            parent=self._base,
            base_type="QWidget",
            label="Axis_2",
            tooltip=tooltip_text,
            parent_widget=self,
            configurable=self.parameter,
            prop="axis_2",
            parameter=self.parameter.descriptors["axis_2"],
        )

        self.add_widget(self.axis_2, key="axis_2")

        self._layout.addWidget(self.molecule._base)
        self._layout.addWidget(self.axis_1._base)
        self._layout.addWidget(self.axis_2._base)

        self.molecule._field.currentTextChanged.connect(self.axis_1.reset_ranges)
        self.molecule._field.currentTextChanged.connect(self.axis_2.reset_ranges)

    def set_value(self, value: tuple[str, int | None, int | None]) -> None:
        self.molecule.value, self.axis_1.value, self.axis_2.value = value

        self.updateValue()

    def trajectory_changed(self):
        """Change molecule preview and molecule information."""
        self.parameter.last_deps = self.parameter._get_deps(self._configurable)
        self.molecule.trajectory_changed(self.get_widget_deps())
        self.molecule.updateValue()
        self.axis_1.updateValue()
        self.axis_2.updateValue()

    @property
    def selected_mol(self) -> str | None:
        return self.molecule.selected_mol

    def get_widget_value(self) -> tuple[str, int | None, int | None]:
        """Widgets handle updates"""
        return self.molecule.value, self.axis_1.value, self.axis_2.value
