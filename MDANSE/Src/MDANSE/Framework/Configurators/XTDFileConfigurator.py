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
import collections
import xml.etree.ElementTree as ElementTree

import numpy as np

from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.Mathematics.Graph import Graph
from MDANSE.Framework.Configurators.FileWithAtomDataConfigurator import (
    FileWithAtomDataConfigurator,
)
from MDANSE.Framework.AtomMapping import AtomLabel, get_element_from_mapping


class XTDFileConfigurator(FileWithAtomDataConfigurator):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self._atoms = None

        self._chemicalSystem = None

        self._pbc = False

        self._cell = None

    @property
    def clusters(self):
        return self._clusters

    @property
    def chemicalSystem(self):
        return self._chemicalSystem

    @property
    def pbc(self):
        return self._pbc

    @property
    def cell(self):
        return self._cell

    def parse(self):
        """
        Parse the xtd file that is basically xml files with nodes that contains informations about the
        topology of the molecular system.
        """

        self._file = ElementTree.parse(self["filename"])

        ROOT = self._file.getroot()

        SPACEGROUP = list(ROOT.iter("SpaceGroup"))

        if SPACEGROUP:
            self._pbc = True
            SPACEGROUP = SPACEGROUP[0]
            self._cell = np.empty((3, 3), dtype=np.float64)
            self._cell[0, :] = SPACEGROUP.attrib["AVector"].split(",")
            self._cell[1, :] = SPACEGROUP.attrib["BVector"].split(",")
            self._cell[2, :] = SPACEGROUP.attrib["CVector"].split(",")
            self._cell *= measure(1.0, "ang").toval("nm")
            self._cell = UnitCell(self._cell)

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

        comp = 0
        for node in ROOT.iter("Bond"):
            idx = int(node.attrib["ID"])

            imageOf = node.attrib.get("ImageOf", None)

            if imageOf is None:
                bondsMapping[idx] = [
                    atomsMapping[int(v)] for v in node.attrib["Connects"].split(",")
                ]
                idx1, idx2 = bondsMapping[idx]
                self._atoms[idx1]["bonded_to"].add(idx2)
                self._atoms[idx2]["bonded_to"].add(idx1)

    def build_chemical_system(self, aliases):
        self._chemicalSystem = ChemicalSystem()

        coordinates = np.empty((self._nAtoms, 3), dtype=np.float64)

        graph = Graph()

        for idx, at in list(self._atoms.items()):
            graph.add_node(name=idx, **at)

        for idx, at in list(self._atoms.items()):
            for bat in at["bonded_to"]:
                graph.add_link(idx, bat)

        clusters = graph.build_connected_components()

        for cluster in clusters:
            bruteFormula = collections.defaultdict(lambda: 0)

            atoms = []
            for node in cluster:
                symbol = node.element
                name = node.atom_name
                element = get_element_from_mapping(aliases, symbol, type=name)
                at = Atom(symbol=element, name=name, xtdIndex=node.xtd_index)
                at.index = node.index
                coordinates[at.index] = node.xyz
                bruteFormula[element] += 1
                atoms.append(at)
            name = "".join(["%s%d" % (k, v) for k, v in sorted(bruteFormula.items())])
            ac = AtomCluster(name, atoms)
            self._chemicalSystem.add_chemical_entity(ac)

        if self._pbc:
            boxConf = PeriodicBoxConfiguration(
                self._chemicalSystem, coordinates, self._cell
            )
            realConf = boxConf.to_real_configuration()
        else:
            coordinates *= measure(1.0, "ang").toval("nm")
            realConf = RealConfiguration(self._chemicalSystem, coordinates, self._cell)

        realConf.fold_coordinates()
        self._chemicalSystem.configuration = realConf

    def get_atom_labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        labels = []
        for info in self._atoms.values():
            label = AtomLabel(info["element"], type=info["atom_name"])
            if label not in labels:
                labels.append(label)
        return labels

    def get_atom_charges(self) -> np.ndarray:
        """Returns an array of partial electric charges

        Returns
        -------
        np.ndarray
            array of floats, one value per atom
        """
        charges = np.array([info["charge"] for info in self._atoms.values()])
        return charges
