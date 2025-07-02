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

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QComboBox

from MDANSE_GUI.InputWidgets.MoleculeWidget import MoleculeWidget


class MoleculeAndAxisWidget(MoleculeWidget):
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
        super().__init__(*args, index_boxes=2, **kwargs)
        self.enable_combo_boxes()
        for cbox in self.index_combo_boxes:
            cbox.currentIndexChanged.connect(self.enable_combo_boxes)
        self._field.currentTextChanged.connect(self.update_combo_boxes)

    @Slot()
    def molecule_changed(self):
        """Update atom index combo boxes."""
        super().molecule_changed()
        self.update_combo_boxes()

    @Slot()
    def update_combo_boxes(self):
        """Set new atom index limits on molecule change."""
        if self.selected_mol is None:
            for cbox in self.index_combo_boxes:
                cbox.clear()
                cbox.addItems(["None"])
                cbox.setCurrentText("None")
                cbox.setEnabled(False)
            return
        n_atoms = len(self.selected_mol["atom_indices"])
        index_elements = ["None"]
        index_elements.extend(str(x) for x in range(n_atoms))
        for box_index, cbox in enumerate(self.index_combo_boxes):
            cbox: QComboBox
            current_value = cbox.currentText()
            cbox.clear()
            cbox.addItems(index_elements)
            cbox.setCurrentText("None") if box_index else cbox.setCurrentText("0")
            try:
                numval = int(current_value)
            except (TypeError, ValueError):
                continue
            if numval in range(n_atoms):
                cbox.setCurrentText(current_value)

    def enable_combo_boxes(self):
        """Activate or deactivate combo boxes based on other inputs.

        The combo boxes of atom index are disabled if no molecule has been
        selected. If the first index is already set to 'None', the second
        combo box is disabled, since its index value will not be used.
        """
        if self.selected_mol is None:
            for cbox in self.index_combo_boxes:
                cbox.setEnabled(False)
            return
        for cbox in self.index_combo_boxes:
            cbox.setEnabled(True)
        if self.index_combo_boxes[0].currentText() == "None":
            self.index_combo_boxes[1].setEnabled(False)

    @staticmethod
    def parse_combo_box(cbox: QComboBox) -> int | None:
        try:
            return int(cbox.currentText())
        except (TypeError, ValueError):
            return None

    def get_widget_value(self) -> tuple[str, int | None, int | None]:
        """Get the molecule name and atom indices.

        Returns
        -------
        tuple[str, int | None, int | None]
            Molecule name, optional atom index 1, optional atom index 2

        """
        return (
            super().get_widget_value(),
            *map(self.parse_combo_box, self.index_combo_boxes),
        )
