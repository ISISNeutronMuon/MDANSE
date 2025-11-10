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

import rdkit.Chem as chem
import rdkit.Chem.AllChem as allchem
import rdkit.Chem.Draw as draw
from PIL.ImageQt import ImageQt
from qtpy.QtCore import QObject
from qtpy.QtGui import QFont, QPixmap
from qtpy.QtWidgets import QDialog, QLabel, QVBoxLayout

from MDANSE.MolecularDynamics.Trajectory import Trajectory


class MoleculePreviewWidget(QDialog):
    """Shows the structure of a single molecule."""

    def __init__(
        self,
        parent: QObject | None,
        molecule_information: dict[str, Any],
        molecule_name: str,
        atom_database: Trajectory,
        max_atom_limit: int = 300,
    ):
        """Create the dialog and set up the widgets.

        Parameters
        ----------
        parent : Union[QObject, None]
            parent in the Qt object hierarchy, optional
        molecule_information : dict[str, Any]
            dictionary of collected molecule properies
        molecule_name : str
            molecule name as used in MDANSE
        atom_database : Trajectory
            trajectory instance, for looking up atom properties
        max_atom_limit : int,
            molecules with more atoms than this will not be drawn

        """
        super().__init__(parent)
        self.setWindowTitle("Molecule Preview")
        self.resize(800, 600)
        self.max_atom_limit = max_atom_limit
        self.axes = []
        self.bond_mapping = {}
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.mol_name = molecule_name
        self.mol_info = molecule_information
        self.atom_database = atom_database
        self.image_label = QLabel(self)
        self.text_label = QLabel(self)
        font = QFont("Arial", 12)
        self.text_label.setFont(font)
        self.text_label.setWordWrap(True)
        layout.addWidget(self.image_label)
        layout.addWidget(self.text_label)
        self.update_text_label()
        self.show_formula()

    def update_text_label(self):
        """Show the molecule information as text."""
        info_text = f"Molecule name: {self.mol_name}\n"
        for key, value in self.mol_info["atom_number"].items():
            info_text += f"Number of {key} atoms: {value}\n"
        info_text += f"Number of such molecules in trajectory: {self.mol_info['no_of_molecules']}\n"
        self.text_label.setText(info_text)

    def prepare_rdkit_molecule(self) -> chem.RWMol | None:
        """Create an rdkit molecule from the selected atoms."""
        if len(self.mol_info["atom_indices"]) > self.max_atom_limit:
            self.image_label.clear()
            self.image_label.setText("Molecule is too large for preview")
            return None
        self.image_label.setText("")
        large_molecule = self.atom_database.chemical_system.rdkit_mol
        submolecule = chem.RWMol()
        mapping = {}
        for index in self.mol_info["atom_indices"]:
            new_index = submolecule.AddAtom(large_molecule.GetAtomWithIdx(index))
            mapping[index] = new_index
        for bond in self.mol_info["bond_list"]:
            i, j = mapping[bond[0]], mapping[bond[1]]
            rdkit_bond = large_molecule.GetBondBetweenAtoms(bond[0], bond[1])
            bond_type = (
                rdkit_bond.GetBondType()
                if rdkit_bond is not None
                else chem.rdchem.BondType.UNSPECIFIED
            )
            submolecule.AddBond(i, j, bond_type)
        allchem.Compute2DCoords(submolecule)
        return submolecule

    def show_formula(self):
        """Draw the molecule."""
        submolecule = self.prepare_rdkit_molecule()
        draw_options = draw.MolDrawOptions()
        draw_options.addAtomIndices = True
        pil_image = draw.MolToImage(submolecule, size=(600, 600), options=draw_options)
        qt_image = ImageQt(pil_image).copy()
        pixmap = QPixmap.fromImage(qt_image)
        self.image_label.setPixmap(pixmap)
