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

from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple, NoReturn
from xml.etree import ElementTree

import numpy as np
from more_itertools import first

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.util_types import FloatArray

from .Parser import Parser


class Atom(NamedTuple):
    name: str
    index: int
    xtd_index: int
    bonded_to: set[int]
    element: str
    xyz: FloatArray
    charge: float


class XTDFile(Parser):
    def __init__(self, filename: Path | str):
        """
        Parse the xtd file that is basically xml files with nodes that contains informations about the
        topology of the molecular system.
        """
        super().__init__(filename)

        file = ElementTree.parse(self.filename)
        root = file.getroot()
        spacegroup = first(root.iter("SpaceGroup"), None)

        self.pbc = spacegroup is not None

        if self.pbc:
            self.cell = np.array(
                [spacegroup.attrib[f"{dim}Vector"].split(",") for dim in "ABC"],
                dtype=np.float64,
            )
            self.cell *= measure(1.0, "ang").toval("nm")
            self.cell = UnitCell(self.cell)

        self._atoms: dict[int, Atom] = {}
        atoms_mapping: dict[int, int] = {}

        for comp, node in enumerate(root.iter("Atom3d")):
            idx = int(node.attrib["ID"])

            if img := node.attrib.get("ImageOf"):
                atoms_mapping[idx] = int(img)
                continue

            atoms_mapping[idx] = idx

            element = first(self._get_comma_prop(node, "Components")).strip()

            name = node.attrib.get("Name", "").strip()
            if not name:
                name = node.attrib.get("ForcefieldType", "").strip()
                if name:
                    name += "_ff"
                else:
                    name = element + "_el"

            atom = Atom(
                name=name,
                index=comp,
                xtd_index=idx,
                element=element,
                xyz=np.fromiter(
                    self._get_comma_prop(node, "XYZ"), count=3, dtype=np.float64
                ),
                charge=float(node.attrib.get("Charge", 0.0)),
                bonded_to=set(),
            )

            self._atoms[idx] = atom

        self._bonds = []

        for node in root.iter("Bond"):
            if "ImageOf" in node.attrib:
                continue

            idx1, idx2 = self._get_comma_prop(node, "Connects", int, atoms_mapping)
            atm1, atm2 = self._atoms[idx1], self._atoms[idx2]
            self._bonds.append((atm1.index, atm2.index))
            atm1.bonded_to.add(idx2)
            atm2.bonded_to.add(idx1)

        self._clusters = [
            [
                prop
                for prop in self._get_comma_prop(
                    node, "Children", int, atoms_mapping, skip_missing=True
                )
                if prop is not None
            ]
            for node in root.iter("Molecule")
            if "ImageOf" not in node.attrib
        ]

    @staticmethod
    def _get_comma_prop(
        node,
        key: str,
        to_type: type = str,
        retrieve: dict | None = None,
        skip_missing: bool = False,
    ):
        data = map(to_type, node.attrib[key].split(","))

        if retrieve is None:
            return data
        return (retrieve.get(key) for key in data)

    @property
    def n_atoms(self) -> int:
        return len(self._atoms)

    @property
    def element_list(self) -> list[str]:
        return [atom.element for atom in self._atoms.values()]

    @property
    def frames(self) -> NoReturn:
        raise StopIteration

    @property
    def atom_labels(self) -> Iterable[AtomLabel]:
        """Return the set of atom labels.

        Yields
        ------
        AtomLabel
            An atom label.
        """
        for atom in self._atoms.values():
            yield AtomLabel(atom.element, type=atom.name)
