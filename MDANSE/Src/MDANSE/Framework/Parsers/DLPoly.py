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
from os import SEEK_SET
from pathlib import Path
from typing import NamedTuple, TextIO

import numpy as np
from more_itertools import consume as drop
from more_itertools import first, first_true, ilen, split_at, split_before, take

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import AtomLabel, get_element_from_mapping
from MDANSE.Framework.Units import measure
from MDANSE.IO.IOUtils import strip_comments
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.util_types import FloatArray

from .Parser import Parser


class Molecule(NamedTuple):
    name: str
    n_mols: int
    n_atoms: int
    species: FloatArray
    masses: FloatArray
    charges: FloatArray
    bonds: list[tuple[int, int]]


class FieldFileError(Exception):
    pass


class HistoryFile(Parser):
    UNIT_CONV = {
        "length": measure(1.0, "ang").toval("nm"),
        "positions": measure(1.0, "ang").toval("nm"),
        "velocities": measure(1.0, "ang/ps").toval("nm/ps"),
        "gradients": measure(1.0, "Da ang / ps2").toval("Da nm / ps2"),
    }

    n_frames = None

    def __init__(self, filename: Path | str):
        super().__init__(filename)

        self.filename = filename

        self._first_step = None
        self._time_step = None

        with open(self.filename, encoding="utf-8") as file:
            tmp = split_before(file, lambda line: line.startswith("timestep"))
            self.read_header(next(tmp))

            frame = self.parse_step(first(tmp))
            self.atoms = frame["spec"]

            self.n_frames = ilen(tmp) + 1

    def read_header(self, data: list[str]):
        # Drop comment

        self.keytrj, self.imcon, self.natm = map(int, data[1].split()[:3])

    def parse_step(self, step: list[str]):
        accum = {}
        accum["true_step"] = int(step[0].split()[1])

        if self._first_step is None:
            self._first_step = accum["true_step"]
            self._time_step = float(step[0].split()[5])

        accum["step"] = accum["true_step"] - self._first_step
        accum["time"] = accum["step"] * self._time_step

        if self.imcon:
            cell = np.array([line.split() for line in step[1:4]], dtype=np.float64).T
            cell *= self.UNIT_CONV["length"]
            accum["unit_cell"] = UnitCell(cell)
        else:
            accum["unit_cell"] = None

        accum["spec"] = [None] * self.natm
        accum["ind"] = np.empty(self.natm, dtype=int)
        accum["charge"] = np.empty(self.natm, dtype=float)
        for i, line in enumerate(map(str.split, step[4 :: self.keytrj + 2])):
            spec, ind, _mass, charge, *_rsd = line
            ref = int(ind) - 1
            accum["ind"][i] = int(ind)
            accum["spec"][ref] = spec
            accum["charge"][ref] = float(charge)

        keys = ("positions", "velocities", "gradients")[: self.keytrj + 1]

        for i, key in enumerate(keys, 1):
            accum[key] = np.array(
                list(map(str.split, step[4 + i :: self.keytrj + 2])), dtype=float
            )

        ref = accum["ind"] - 1
        for key in keys:
            accum[key] = accum[key][ref, :] * self.UNIT_CONV[key]

        return accum

    @property
    def element_list(self) -> list[str]:
        return self.atoms

    @property
    def frames(self):
        with open(self.filename, encoding="utf-8") as file:
            drop(file, 2)

            steps = split_before(file, lambda line: line.startswith("timestep"))
            yield from map(self.parse_step, steps)


class FieldFile:
    """The DL_POLY field file configurator."""

    def __init__(self, filename):
        # The FIELD file is opened for reading, its contents stored into |lines| and then closed.
        self.filename = filename
        with open(self.filename, encoding="utf-8") as unit:
            lines = strip_comments(unit)

            self.title = next(lines)
            self.units = next(lines)

            # Extract the number of molecular types
            self.n_molecular_types = int(next(lines).rsplit(maxsplit=1)[-1])

            molecules = split_at(
                lines,
                lambda line: line.upper() == "FINISH",
                maxsplit=self.n_molecular_types,
            )

            self.molecules = [
                self.parse_molecule(molecule)
                for molecule in take(self.n_molecular_types, molecules)
            ]
            molecules = iter(next(molecules))

        if self.n_molecular_types != len(self.molecules):
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
                    repeat, _frozen = map(int, rep_froz[:2])

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

    @property
    def labels(self) -> list[AtomLabel]:
        return list(self.atom_labels)

    @property
    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for molecule in self.molecules:
            for atm_label, mass in zip(molecule.species, molecule.masses, strict=True):
                yield AtomLabel(atm_label, molecule=molecule.name, mass=mass)

    def get_atom_charges(self) -> FloatArray:
        """Returns an array of partial electric charges

        Returns
        -------
        FloatArray
            array of floats, one value per atom
        """
        charge_groups = [
            np.repeat(molecule.charges, molecule.n_mols) for molecule in self.molecules
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

        for molecule in self.molecules:
            curr_element_list = [
                get_element_from_mapping(
                    aliases, name, molecule=molecule.name, mass=mass
                )
                for name, mass in zip(molecule.species, molecule.masses, strict=True)
            ]
            curr_name_list = molecule.species
            curr_cluster = np.arange(molecule.n_atoms, dtype=int)

            # Bonds 0-indexed in RDKit
            curr_bonds = np.array(molecule.bonds, dtype=int) - 1

            for _ in range(molecule.n_mols):
                element_list.extend(curr_element_list)
                name_list.extend(curr_name_list)
                bonds.extend(map(tuple, curr_bonds + curr_n))

                if len(curr_cluster) > 1:
                    clusters.append(list(curr_cluster + curr_n))

                curr_n += molecule.n_atoms

        chemical_system.initialise_atoms(element_list, name_list)
        chemical_system.add_clusters(clusters)
        chemical_system.add_bonds(bonds)
