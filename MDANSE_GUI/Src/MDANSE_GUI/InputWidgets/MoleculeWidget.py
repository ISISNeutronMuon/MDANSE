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

from typing import Union

import numpy as np
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QComboBox, QLabel, QPushButton

from MDANSE_GUI.InputWidgets.MoleculePreviewWidget import MoleculePreviewWidget
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class MoleculeWidget(WidgetBase):
    """MDANSE input widget for selecting a molecule type in a trajectory."""

    def __init__(self, *args, index_boxes: int = 0, **kwargs):
        """Populate the combo box with valid molecule names."""
        super().__init__(*args, **kwargs)
        self.index_combo_boxes = []
        configurator = kwargs.get("configurator")
        trajectory_configurator = kwargs.get("trajectory_configurator")
        default_option = ""
        if trajectory_configurator is not None:
            option_list = trajectory_configurator[
                "instance"
            ].chemical_system.unique_molecules()
            if len(option_list) > 0:
                default_option = option_list[0]
        elif configurator is None:
            option_list = kwargs.get("choices", [])
        else:
            option_list = configurator.choices
            default_option = configurator.default
        traj_config = self._configurator.configurable[
            self._configurator.dependencies["trajectory"]
        ]
        trajectory = traj_config["instance"]
        unique_molecules = trajectory.chemical_system.unique_molecules()
        traj_bond_list = trajectory.chemical_system._bonds
        self.atom_database = trajectory
        self.mol_dict = {}
        for mol_name in unique_molecules:
            no_of_molecules = len(trajectory.chemical_system._clusters[mol_name])
            atom_indices = trajectory.chemical_system._clusters[mol_name][0]
            atom_symbols = [
                trajectory.chemical_system.atom_list[index] for index in atom_indices
            ]
            unique_atoms, atom_counts = np.unique(atom_symbols, return_counts=True)
            atom_counts = {
                unique_atoms[n]: atom_counts[n] for n in range(len(unique_atoms))
            }
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
                "bond_list": bonds,
            }

        self.field = QComboBox(self._base)
        self.field.addItems(option_list)
        self.field.setCurrentText(default_option)
        self.selected_name = self.field.currentText()
        self.selected_mol = self.mol_dict.get(self.selected_name, None)
        self.field.currentTextChanged.connect(self.updateValue)
        self.field.currentTextChanged.connect(self.molecule_changed)
        initial_num_atoms = len(
            self.mol_dict.get(default_option, {}).get("atom_indices", []),
        )
        index_elements = ["None"]
        index_elements.extend(str(x) for x in range(initial_num_atoms))
        for box_index in range(index_boxes):
            index_box = QComboBox(self._base)
            index_box.setEditable(False)
            index_box.addItems(index_elements)
            index_box.setCurrentText("None") if box_index else index_box.setCurrentText(
                "0",
            )
            self.index_combo_boxes.append(index_box)
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
        self.field.setToolTip(tooltip_text)
        self._field = self.field
        self._layout.addWidget(self.field)
        for nbox, cbox in enumerate(self.index_combo_boxes):
            self._layout.addWidget(QLabel(f"Atom {nbox + 1}:"))
            self._layout.addWidget(cbox)
        self._layout.addWidget(button)
        self._configurator = configurator
        self.valid_changed.connect(self.toggle_button)
        self.default_labels()
        self.update_labels()
        self.updateValue()

    @Slot()
    def molecule_changed(self):
        """Change molecule preview and molecule information."""
        self.selected_name = self.field.currentText()
        try:
            self.selected_mol = self.mol_dict[self.selected_name]
        except KeyError:
            self.selected_mol = None
        else:
            self.window = MoleculePreviewWidget(
                self._base,
                self.selected_mol,
                self.selected_name,
                self.atom_database,
            )

    @Slot()
    def button_clicked(self):
        """Open a window that shows a preview of selected molecule."""
        if self.selected_mol is None:
            return
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

    def configure_using_default(self):
        """Do nothing in the case of this widget."""

    def default_labels(self):
        """Set labels to default values.

        Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured.
        """
        if self._label_text == "":
            self._label_text = "ComboWidget"
        if self._tooltip == "":
            self._tooltip = "You only have one option. Choose wisely."

    def toggle_button(self):
        """Enable the button only if molecules are present."""
        self.view_button.setEnabled(self.field.count())

    def get_widget_value(self) -> str | None:
        """Return the currently selected molecule name."""
        mol_key = self._field.currentText()
        if mol_key in self.mol_dict:
            return mol_key
        return None
