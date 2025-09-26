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
from collections.abc import Iterable

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import AtomLabel, get_element_from_mapping

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator

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

# mapping of some commonly used atom names to their actual atom types
# taken from MDAnalysis/guesser/tables.py
NAME_TO_TYPE = {
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


class PDBFileConfigurator(FileWithAtomDataConfigurator):
    def parse(self) -> None:
        """Get the atom data from the PDB file."""
        self.atoms = []
        with open(self["filename"], encoding="utf-8") as source:
            for line in source:
                if line.startswith(("ATOM", "HETATM")):
                    name = line[ATOM_LINE_RECORDS["atom_name"]].strip()
                    res_name = line[ATOM_LINE_RECORDS["residue_name"]].strip()
                    res_num = line[ATOM_LINE_RECORDS["residue_number"]].strip()
                    if name in NAME_TO_TYPE:
                        element = NAME_TO_TYPE[name]
                    else:
                        element = max(
                            re.findall("([A-Za-z][A-Za-z]*)", name), key=len
                        ).capitalize()
                        # take the first character first because things like CA are
                        # carbon atoms
                        if element[0] in ATOMS_DATABASE.atoms:
                            element = element[0]
                        elif element[:2] in ATOMS_DATABASE.atoms:
                            element = element[:2]
                        else:
                            element = name
                    self.atoms.append((element, name, res_name, res_num))

                if line.startswith("END"):
                    break

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
        label_dict = {}
        clusters = {}

        chemical_system = ChemicalSystem()
        for atom_number, (element, name, res_name, res_num) in enumerate(self.atoms):
            element_list.append(
                get_element_from_mapping(aliases, element, name=name, residue=res_name)
            )

            label_dict.setdefault(res_name, [])
            label_dict[res_name].append(atom_number)
            name_list.append(name)

            try:
                residue_number = int(res_num)
            except ValueError:
                try:
                    residue_number = int(res_num, base=16)
                except ValueError:
                    continue

            idx = (res_name, residue_number)
            clusters.setdefault(idx, [])
            clusters[idx].append(atom_number)

        chemical_system.initialise_atoms(element_list, name_list)
        chemical_system.add_labels(label_dict)
        chemical_system.add_clusters(clusters.values())
        return chemical_system

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for element, name, res_name, _ in self.atoms:
            yield AtomLabel(
                element,
                name=name,
                residue=res_name,
            )
