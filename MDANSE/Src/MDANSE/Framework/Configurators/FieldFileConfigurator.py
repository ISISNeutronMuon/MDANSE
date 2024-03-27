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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Scientific Computing Group at ILL (see AUTHORS)
import re

from MDANSE.Chemistry.ChemicalEntity import (
    Atom,
    AtomCluster,
)
from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import get_element_from_mapping, AtomLabel

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class FieldFileError(Error):
    pass


class FieldFileConfigurator(FileWithAtomDataConfigurator):
    """The DL_POLY field file configurator."""

    def parse(self):
        # The FIELD file is opened for reading, its contents stored into |lines| and then closed.
        with open(self["filename"], "r") as unit:
            # Read and remove the empty and comments lines from the contents of the FIELD file.
            lines = [
                line.strip()
                for line in unit.readlines()
                if line.strip() and not re.match("#", line)
            ]

        self["title"] = lines.pop(0)

        self["units"] = lines.pop(0)

        # Extract the number of molecular types
        _, self["n_molecular_types"] = re.match(
            "(molecules|molecular types)\s+(\d+)", lines.pop(0), re.IGNORECASE
        ).groups()

        self["n_molecular_types"] = int(self["n_molecular_types"])

        molBlocks = [
            i for i, line in enumerate(lines) if re.match("finish", line, re.IGNORECASE)
        ]

        if self["n_molecular_types"] != len(molBlocks):
            raise FieldFileError("Error in the definition of the molecular types")

        self["molecules"] = []

        first = 0

        for last in molBlocks:
            moleculeName = lines[first]

            # Extract the number of molecular types
            nMolecules = re.match(
                "nummols\s+(\d+)", lines[first + 1], re.IGNORECASE
            ).groups()[0]
            nMolecules = int(nMolecules)

            for i in range(first + 2, last):
                match = re.match("atoms\s+(\d+)", lines[i], re.IGNORECASE)
                if match:
                    nAtoms = int(match.groups()[0])

                    sumAtoms = 0

                    comp = i + 1

                    atoms = []
                    masses = []

                    while sumAtoms < nAtoms:
                        sitnam = lines[comp][:8].strip()

                        vals = lines[comp][8:].split()

                        try:
                            nrept = int(vals[2])
                        except IndexError:
                            nrept = 1

                        masses.extend([float(vals[0])] * nrept)
                        atoms.extend([sitnam] * nrept)

                        sumAtoms += nrept

                        comp += 1

                    self["molecules"].append([moleculeName, nMolecules, atoms, masses])

                    break

            first = last + 1

    def get_atom_labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        labels = []
        for mol_name, _, atomic_contents, masses in self["molecules"]:
            for atm_label, mass in zip(atomic_contents, masses):
                label = AtomLabel(atm_label, molecule=mol_name, mass=mass)
                if label not in labels:
                    labels.append(label)
        return labels

    def build_chemical_system(self, chemicalSystem, aliases):
        chemicalEntities = []

        for db_name, nMolecules, atomic_contents, masses in self["molecules"]:
            # Loops over the number of molecules of the current type.
            for i in range(nMolecules):
                # This list will contains the instances of the atoms of the molecule.
                atoms = []
                # Loops over the atom of the molecule.
                for j, (name, mass) in enumerate(zip(atomic_contents, masses)):
                    # The atom is created.
                    element = get_element_from_mapping(
                        aliases, name, molecule=db_name, mass=mass
                    )
                    a = Atom(symbol=element, name="%s_%s_%s" % (db_name, name, j))
                    atoms.append(a)

                if len(atoms) > 1:
                    ac = AtomCluster("{:s}".format(db_name), atoms)
                    chemicalEntities.append(ac)
                else:
                    chemicalEntities.append(atoms[0])

        for ce in chemicalEntities:
            chemicalSystem.add_chemical_entity(ce)
