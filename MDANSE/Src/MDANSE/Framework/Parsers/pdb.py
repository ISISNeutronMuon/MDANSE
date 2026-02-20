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

import re
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import NamedTuple

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import AtomLabel, get_element_from_mapping
from MDANSE.Framework.Parsers.Parser import Parser


class PDBAtom(NamedTuple):
    """PDB ATOM/HETATM type."""

    element: str
    name: str
    residue_name: str
    residue_number: str

    @property
    def residue_id(self) -> int:
        try:
            return int(self.residue_number)
        except ValueError:
            return int(self.residue_number, base=16)

    @property
    def residue_index(self) -> tuple[str, int]:
        return self.residue_name, self.residue_id


class PDBFile(Parser):
    _ATOM_LINE_RECORDS = {
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

    # mapping of some commonly used atom names to their actual atom types
    # taken from MDAnalysis/guesser/tables.py
    _NAME_TO_TYPE = {
        "BR": "Br",
        "CAL": "Ca",
        "C0": "Ca",
        "CA2+": "Ca",
        "CLA": "Cl",
        "CLAL": "Cl",
        "CL": "Cl",
        "CL-": "Cl",
        "IOD": "I",
        "FE": "Fe",
        "FE2": "Fe",
        "LIT": "Li",
        "LI": "Li",
        "LI+": "Li",
        "QL": "Li",
        "MG": "Mg",
        "MG2+": "Mg",
        "K": "K",
        "POT": "K",
        "K+": "K",
        "QK": "K",
        "SOD": "Na",
        "NA": "Na",
        "NA+": "Na",
        "QN": "Na",
        "ZN": "Zn",
        "CU": "Cu",
        "CS": "Cs",
        "CS+": "Cs",
        "CES": "Cs",
        "QC": "Ce",
        "RB": "Rb",
        "QR": "Rb",
        "BC": "C",
        "AC": "C",
    }

    def __init__(self, filename: Path | str, **kwargs):
        super().__init__(filename)
        self.parse()

    @classmethod
    def _parse_atom_line(cls, line: str) -> dict[str, str]:
        return {key: line[loc].strip() for key, loc in cls._ATOM_LINE_RECORDS.items()}

    @staticmethod
    def _parse_name(name: str) -> str:
        trial = max(re.findall(r"[A-Za-z]+", name), key=len).capitalize()
        if trial[0] in ATOMS_DATABASE.atoms:
            return trial[0]
        if trial[:2] in ATOMS_DATABASE.atoms:
            return trial[:2]

        return name

    def parse(self) -> None:
        """Get the atom data from the PDB file."""
        self.atoms: list[PDBAtom] = []

        with open(self.filename, encoding="utf-8") as source:
            for line in source:
                if line.startswith("END"):
                    break

                if line.startswith(("ATOM", "HETATM")):
                    info = self._parse_atom_line(line)
                    name = info["atom_name"]
                    element = (
                        self._NAME_TO_TYPE[name]
                        if name in self._NAME_TO_TYPE
                        else self._parse_name(name)
                    )
                    self.atoms.append(
                        PDBAtom(
                            element,
                            name,
                            info["residue_name"],
                            info["residue_number"],
                        )
                    )

    def build_chemical_system(self, aliases) -> ChemicalSystem:
        """
        Build a :class:`~MDANSE.Chemistry.ChemicalSystem.ChemicalSystem`.

        Parameters
        ----------
        aliases : dict[str, dict[str, str]]
            Mapping of atomic aliases to elements.

        Returns
        -------
        ChemicalSystem
            The chemical system built from the pdb file data.
        """

        element_list = []
        name_list = []
        label_dict = defaultdict(list)
        clusters = defaultdict(list)

        chemical_system = ChemicalSystem()
        for atom_number, atom in enumerate(self.atoms):
            element_list.append(
                get_element_from_mapping(
                    aliases,
                    atom.element,
                    name=atom.name,
                    residue=atom.residue_name,
                )
            )

            label_dict[atom.residue_name].append(atom_number)
            name_list.append(atom.name)

            clusters[atom.residue_index].append(atom_number)

        chemical_system.initialise_atoms(element_list, name_list)
        chemical_system.add_labels(label_dict)
        chemical_system.add_clusters(clusters.values())
        return chemical_system

    @property
    def frames(self) -> Iterator:
        """Return all frames contained in the file as a sequential iterator."""
        return iter([])

    @property
    def element_list(self) -> list[str]:
        return [atom.element for atom in self.atoms]

    @property
    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for atom in self.atoms:
            yield AtomLabel(
                atom.element,
                name=atom.name,
                residue=atom.residue_name,
            )
