#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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

from collections.abc import Generator, Iterable

import numpy as np
from ase.io import read as ase_read

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.MLogging import LOG

ATOM_LINE_RECORDS = {
    "record_name": slice(0, 6),
    "atom_number": slice(6, 11),
    "atom_name": slice(12, 16),
    "location": slice(16, 17),
    "residue_name": slice(17, 20),
    "chain_id": slice(21, 22),
    "residue_number": slice(22, 26),
    "insertion_code": slice(26, 27),
    "pos_x": slice(30, 38),
    "pos_y": slice(38, 46),
    "pos_z": slice(46, 54),
    "occupancy": slice(54, 60),
    "temperature_factor": slice(60, 66),
    "element_symbol": slice(76, 78),
    "charge": slice(78, 80),
}


class MinimalPDBReader:
    """
    Basic parser for PDB format files.

    Parameters
    ----------
    filename : str
        Input file to read.
    """

    def __init__(self, filename: str):
        self._unit_cell = None
        cell_params = self.find_unit_cell(filename)
        self.periodic = False

        if cell_params:
            try:
                ase_atoms = ase_read(filename, format="pdb", index=0)
                cell = ase_atoms.get_cell()
            except Exception:
                self.periodic = False
            else:
                self.periodic = True
                self._unit_cell = np.vstack(cell)

        self._chemical_system = ChemicalSystem(filename)
        atom_lines = self.find_atoms(filename)
        self.build_chemical_system(atom_lines)

    def find_unit_cell(self, filename: str, frame_number: int = 0) -> list[float]:
        """
        Find unit cell in PDB file.

        Parameters
        ----------
        filename : str
            File to parse.
        frame_number : int
            Unused, for interface compatibility.

        Returns
        -------
        list[float]
            Unit cell as a,b,c,α,β,γ.
        """
        fail_count = 0

        with open(filename, encoding="utf-8") as source:
            for line in source:
                if line.startswith("CRYST"):
                    cell_line = line
                    break

                if line.startswith("ENDMDL"):
                    fail_count += 1

                    if fail_count > 2:
                        return []
            else:
                return []

        return [float(x) for x in cell_line.split()[1:7]]

    def find_atoms(
        self, filename: str, _frame_number: int = 0
    ) -> Generator[str, None, None]:
        """
        Get all items from PDB file.

        Parameters
        ----------
        filename : str
            File to read.

        Yields
        ------
        str
            Each atom line in PDB file.
        """
        with open(filename, encoding="utf-8") as source:
            for line in source:
                if line.startswith(("ATOM", "HETATM")):
                    yield line

                if line.startswith("END"):
                    break

    def build_chemical_system(self, atom_lines: Iterable[str]) -> None:
        """
        Build a :class:`~MDANSE.Chemistry.ChemicalSystem.ChemicalSystem`.

        Parameters
        ----------
        atom_lines : Iterable[str]
            Lines to read.
        """

        element_slice = ATOM_LINE_RECORDS["element_symbol"]
        name_slice = ATOM_LINE_RECORDS["atom_name"]
        pos_slice = (ATOM_LINE_RECORDS[x] for x in ("pos_x", "pos_y", "pos_z"))
        residue_slice = ATOM_LINE_RECORDS["residue_name"]
        residue_number_slice = ATOM_LINE_RECORDS["residue_number"]

        coordinates = []
        element_list = []
        name_list = []
        label_dict = {}
        clusters = {}

        for atom_number, atom_line in enumerate(atom_lines):
            chemical_element = atom_line[element_slice].strip().capitalize()
            atom_name = atom_line[name_slice]
            processed_atom_name = atom_name[:2].strip()

            if len(processed_atom_name) == 2 and processed_atom_name[0].isnumeric():
                processed_atom_name = processed_atom_name[1]
            processed_atom_name = processed_atom_name.capitalize()

            backup_elements = atom_line.split()[-2:]

            if atom_name[-2:].isnumeric():
                backup_elements.append(atom_name[0])

            for trial in (*backup_elements, chemical_element, processed_atom_name):
                if trial in ATOMS_DATABASE.atoms:
                    element_list.append(trial)
                    break
            else:
                LOG.warning(f"Dummy atom introduced from line {atom_line}")
                element_list.append("Du")

            coordinates.append([float(atom_line[pos]) for pos in pos_slice])

            residue_name = atom_line[residue_slice]
            label_dict.setdefault(residue_name, [])

            label_dict[residue_name].append(atom_number)
            name_list.append(atom_name.strip())

            residue_number_string = atom_line[residue_number_slice]
            try:
                residue_number = int(residue_number_string)
            except ValueError:
                try:
                    residue_number = int(residue_number_string, base=16)
                except ValueError:
                    continue

            idx = (residue_name, residue_number)
            clusters.setdefault(idx, [])
            clusters[idx].append(atom_number)

        self._chemical_system.initialise_atoms(element_list, name_list)
        self._chemical_system.add_labels(label_dict)
        self._chemical_system.add_clusters(clusters.values())
