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
from typing import NamedTuple

import numpy as np
from more_itertools import first_true, split_at, split_before, take
from numpy.typing import NDArray

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import AtomLabel, get_element_from_mapping
from MDANSE.IO.IOUtils import strip_comments
from MDANSE.MLogging import LOG

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class Molecule(NamedTuple):
    name: str
    n_mols: int
    n_atoms: int
    species: NDArray[float]
    masses: NDArray[float]
    charges: NDArray[float]
    bonds: list[tuple[int, int]]


class FieldFileError(Error):
    pass


class FieldFileConfigurator(FileWithAtomDataConfigurator):
    """The DL_POLY field file configurator."""

    def parse(self):
        # The FIELD file is opened for reading, its contents stored into |lines| and then closed.
        with open(self["filename"]) as unit:
            lines = strip_comments(unit)

            self["title"] = next(lines)
            self["units"] = next(lines)

            # Extract the number of molecular types
            self["n_molecular_types"] = int(next(lines).rsplit(maxsplit=1)[-1])

            molecules = split_at(
                lines,
                lambda line: line.upper() == "FINISH",
                maxsplit=self["n_molecular_types"],
            )

            self["molecules"] = [
                self.parse_molecule(molecule)
                for molecule in take(self["n_molecular_types"], molecules)
            ]
            molecules = iter(next(molecules))

        if self["n_molecular_types"] != len(self["molecules"]):
            raise FieldFileError("Error in the definition of the molecular types")

    MOLECULAR_KEYS = (
        "nummol",
        "atoms",
        "shell",
        "constr",
        "pmf",
        "rigid",
        "teth",
        "bonds",
        "angles",
        "dihedr",
        "invers",
    )

    def _find_molecular_key(self, string: str):
        string = string.lower()
        return first_true(
            self.MOLECULAR_KEYS,
            pred=string.startswith,
            default=None,
        )

    def parse_molecule(
        self,
        molecule: Iterable[str],
    ) -> Molecule:
        molecule = iter(molecule)
        molecule_name = next(molecule)
        blocks = split_before(molecule, self._find_molecular_key)

        bonds = []
        n_mols = -1

        for block in map(iter, blocks):
            line = next(block)
            key = self._find_molecular_key(line)
            count = int(line.rsplit(maxsplit=1)[-1])

            LOG.debug("%s: %d", key, count)

            if key == "nummol":
                n_mols = count
            elif key == "atoms":
                n_atoms = count

                specs = np.empty(n_atoms, dtype="U8")
                masses = np.empty(n_atoms, dtype=np.float64)
                charges = np.empty(n_atoms, dtype=np.float64)
                curr = 0

                for atom in block:
                    spec, mass, charge, *rep_froz = (atom + " 1 0").split()
                    repeat, frozen = map(int, rep_froz[:2])

                    current_slice = np.s_[curr : curr + repeat]
                    specs[current_slice] = spec
                    masses[current_slice] = mass
                    charges[current_slice] = charge

                    curr += repeat

            elif key == "bonds":
                n_bonds = count

                bonds = [None] * n_bonds
                for i, bond in enumerate(block):
                    _type, a, b, *_params = bond.split()

                    bonds[i] = a, b

        return Molecule(
            name=molecule_name,
            n_mols=n_mols,
            n_atoms=n_atoms,
            species=specs,
            masses=masses,
            charges=charges,
            bonds=bonds,
        )

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for molecule in self["molecules"]:
            for atm_label, mass in zip(molecule.species, molecule.masses):
                yield AtomLabel(atm_label, molecule=molecule.name, mass=mass)

    def get_atom_charges(self) -> np.ndarray:
        """Returns an array of partial electric charges

        Returns
        -------
        np.ndarray
            array of floats, one value per atom
        """
        charge_groups = [
            np.repeat(molecule.charges, molecule.n_mols)
            for molecule in self["molecules"]
        ]

        return np.concatenate(charge_groups)

    def build_chemical_system(
        self, chemical_system: ChemicalSystem, aliases: dict[str, dict[str, str]]
    ):
        """Parses FIELD file to construct initial system.

        Parameters
        ----------
        chemical_system : ChemicalSystem
            Chemical system to build on.
        aliases : dict[str, dict[str, str]]
            Mapping of atomic aliases to elements.

        Returns
        -------
        ChemicalSystem
            Initialised structure.
        """
        clusters = []
        element_list = []
        name_list = []
        bonds = []
        curr_n = 0

        for molecule in self["molecules"]:
            curr_element_list = [
                get_element_from_mapping(
                    aliases, name, molecule=molecule.name, mass=mass
                )
                for name, mass in zip(molecule.species, molecule.masses)
            ]
            curr_name_list = molecule.species
            curr_cluster = np.arange(molecule.n_atoms, dtype=int)

            # Bonds 0-indexed in RDKit
            curr_bonds = np.array(molecule.bonds, dtype=int) - 1

            for i in range(1, molecule.n_mols + 1):
                element_list.extend(curr_element_list)
                name_list.extend(curr_name_list)
                bonds.extend(map(tuple, curr_bonds + curr_n))

                if len(curr_cluster) > 1:
                    clusters.append(list(curr_cluster + curr_n))

                curr_n += molecule.n_atoms

        chemical_system.initialise_atoms(element_list, name_list)
        chemical_system.add_clusters(clusters)
        chemical_system.add_bonds(bonds)
