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

from collections import Counter
from typing import TYPE_CHECKING

import numpy as np
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QComboBox, QLabel, QPushButton

from MDANSE.Framework.Parameters import Molecule
from MDANSE_GUI.InputWidgets import ComboWidget
from MDANSE_GUI.InputWidgets.MoleculePreviewWidget import MoleculePreviewWidget

if TYPE_CHECKING:
    from MDANSE.Framework.Parameters.UtilTypes import Depends


class MoleculeWidget(ComboWidget):
    """MDANSE input widget for selecting a molecule type in a trajectory."""

    def __init__(self, *args, index_boxes: int = 0, **kwargs):
        """Populate the combo box with valid molecule names."""
        self.mol_dict = {}
        super().__init__(*args, **kwargs)

        self.index_combo_boxes = [QComboBox(self._base) for box in range(index_boxes)]

        self.trajectory_changed()

        self._field.currentTextChanged.connect(self.molecule_changed)

        button = QPushButton(self._base)
        button.setText("Molecule Preview")
        button.clicked.connect(self.button_clicked)

        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = (
                "A single option can be picked out of all the options listed."
            )

        self.view_button = button
        self._field.setToolTip(tooltip_text)

        self._layout.addWidget(self._field)
        for nbox, cbox in enumerate(self.index_combo_boxes):
            self._layout.addWidget(QLabel(f"Atom {nbox + 1}:"))
            self._layout.addWidget(cbox)
        self._layout.addWidget(button)

        self.valid_changed.connect(self.toggle_button)
        self.default_labels()
        self.update_labels()
        self.updateValue()

    @Slot()
    def molecule_changed(self):
        """Change molecule preview and molecule information."""
        self.selected_name = self._field.currentText()
        self.selected_mol = self.mol_dict.get(self.selected_name, None)

        if self.selected_mol is not None:
            self.window = MoleculePreviewWidget(
                self._base,
                self.selected_mol,
                self.selected_name,
                self.trajectory,
            )

    @Slot()
    def button_clicked(self):
        """Open a window that shows a preview of selected molecule."""
        self.molecule_changed()
        if self.selected_mol is None:
            return
        if self.window is None:
            self.window = MoleculePreviewWidget(
                self._base,
                self.selected_mol,
                self.selected_name,
                self.atom_database,
            )
        if self.window.isVisible():
            self.window.close()
        else:
            self.window.show()

    def trajectory_changed(self, deps: Depends | None = None):
        deps = deps or self.get_widget_deps()

        self.trajectory = deps["choices"].value
        traj_bond_list = self.trajectory.chemical_system._bonds

        self.get_choices()
        self.mol_dict.clear()

        for mol_name in self.choices:
            no_of_molecules = len(self.trajectory.chemical_system._clusters[mol_name])
            atom_indices = self.trajectory.chemical_system._clusters[mol_name][0]
            atom_symbols = [
                self.trajectory.chemical_system.atom_list[index]
                for index in atom_indices
            ]
            atom_counts = Counter(atom_symbols)
            bonds = [
                (bond[0], bond[1])
                for bond in traj_bond_list
                if bond[0] in atom_indices and bond[1] in atom_indices
            ]
            self.mol_dict[mol_name] = {
                "no_of_molecules": no_of_molecules,
                "atom_number": atom_counts,
                "atom_indices": atom_indices,
                "atom_symbols": atom_symbols,
                "num_atoms": len(atom_indices),
                "bond_list": bonds,
            }

        self.molecule_changed()

        if self.selected_mol is not None:
            index_elements = [str(x) for x in range(self.selected_mol["num_atoms"])]
        else:
            index_elements = ["None"]

        for box in self.index_combo_boxes:
            box.clearItems()
            box.setEditable(False)
            box.addItems(index_elements)
            box.setCurrentText("0" if self.selected_mol else "None")

    def default_labels(self):
        """Set labels to default values.

        Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured.
        """
        if not self._label_text:
            self._label_text = "ComboWidget"
        if not self._tooltip:
            self._tooltip = "You only have one option. Choose wisely."

    def toggle_button(self):
        """Enable the button only if molecules are present."""
        self.view_button.setEnabled(self._field.count())

    def get_widget_value(self) -> str | None:
        """Return the currently selected molecule name."""
        mol_key = self._field.currentText()

        if mol_key in self.mol_dict:
            return mol_key
        return None
