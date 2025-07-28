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

import collections
from collections.abc import Iterable
from xml.etree import ElementTree

import numpy as np

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import AtomLabel, get_element_from_mapping
from MDANSE.Framework.Configurators.FileWithAtomDataConfigurator import (
    FileWithAtomDataConfigurator,
)
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class XTDFileConfigurator(FileWithAtomDataConfigurator):
    """Opens and reads an XTD file.

    The information contained in the XTD file will be used
    to construct an instance of ChemicalSystem.
    """

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._atoms = None

        self._chemical_system = None

        self.pbc = False

        self.cell = None

        self._configuration = None

    @property
    def clusters(self):
        return self._chemical_system._clusters

    @property
    def chemicalSystem(self):
        return self._chemical_system

    def parse(self):
        """
        Parse the xtd file that is basically xml files with nodes that contains informations about the
        topology of the molecular system.
        """

        self._file = ElementTree.parse(self["filename"])

        ROOT = self._file.getroot()

        SPACEGROUP = list(ROOT.iter("SpaceGroup"))

        if SPACEGROUP:
            self.pbc = True
            SPACEGROUP = SPACEGROUP[0]
            self.cell = np.empty((3, 3), dtype=np.float64)
            self.cell[0, :] = SPACEGROUP.attrib["AVector"].split(",")
            self.cell[1, :] = SPACEGROUP.attrib["BVector"].split(",")
            self.cell[2, :] = SPACEGROUP.attrib["CVector"].split(",")
            self.cell *= measure(1.0, "ang").toval("nm")
            self.cell = UnitCell(self.cell)

        self._atoms = collections.OrderedDict()

        atomsMapping = {}

        comp = 0
        for node in ROOT.iter("Atom3d"):
            idx = int(node.attrib["ID"])

            imageOf = node.attrib.get("ImageOf", None)

            if imageOf is None:
                atomsMapping[idx] = idx

                info = {}
                info["index"] = comp
                info["xtd_index"] = idx
                info["bonded_to"] = set()
                info["element"] = node.attrib["Components"].split(",")[0].strip()
                info["xyz"] = np.array(node.attrib["XYZ"].split(","), dtype=np.float64)
                try:
                    info["charge"] = float(node.attrib["Charge"])
                except KeyError:
                    info["charge"] = 0.0

                name = node.attrib.get("Name", "").strip()
                if name:
                    info["atom_name"] = name
                else:
                    name = node.attrib.get("ForcefieldType", "").strip()
                    if name:
                        info["atom_name"] = name + "_ff"
                    else:
                        info["atom_name"] = info["element"] + "_el"

                self._atoms[idx] = info

                comp += 1

            else:
                atomsMapping[idx] = int(imageOf)

        self._nAtoms = len(self._atoms)

        bondsMapping = {}
        self._bonds = []

        comp = 0
        for node in ROOT.iter("Bond"):
            idx = int(node.attrib["ID"])

            imageOf = node.attrib.get("ImageOf", None)

            if imageOf is None:
                bondsMapping[idx] = [
                    atomsMapping[int(v)] for v in node.attrib["Connects"].split(",")
                ]
                idx1, idx2 = bondsMapping[idx]
                self._bonds.append(
                    (self._atoms[idx1]["index"], self._atoms[idx2]["index"])
                )
                self._atoms[idx1]["bonded_to"].add(idx2)
                self._atoms[idx2]["bonded_to"].add(idx1)

    def build_chemical_system(self, aliases):
        self._chemical_system = ChemicalSystem()

        coordinates = np.array(
            [atom["xyz"] for atom in self._atoms.values()], dtype=np.float64
        )
        element_list = [atom["element"] for atom in self._atoms.values()]
        name_list = [atom["atom_name"] for atom in self._atoms.values()]
        unique_labels = set(name_list)
        label_dict = {label: [] for label in unique_labels}
        for temp_index, atom in enumerate(self._atoms.values()):
            label_dict[atom["atom_name"]].append(temp_index)

        self._chemical_system.initialise_atoms(element_list, name_list)
        self._chemical_system.add_bonds(self._bonds)
        self._chemical_system.add_labels(label_dict)
        self._chemical_system.find_clusters_from_bonds()

        if self.pbc:
            boxConf = PeriodicBoxConfiguration(
                self._chemical_system, coordinates, self.cell
            )
            real_conf = boxConf.to_real_configuration()
        else:
            coordinates *= measure(1.0, "ang").toval("nm")
            real_conf = RealConfiguration(
                self._chemical_system, coordinates, unit_cell=self._cell
            )

        real_conf.fold_coordinates()
        self._configuration = real_conf

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for info in self._atoms.values():
            yield AtomLabel(info["element"], type=info["atom_name"])

    def get_atom_charges(self) -> np.ndarray:
        """Returns an array of partial electric charges

        Returns
        -------
        np.ndarray
            array of floats, one value per atom
        """
        charges = np.array([info["charge"] for info in self._atoms.values()])
        return charges
