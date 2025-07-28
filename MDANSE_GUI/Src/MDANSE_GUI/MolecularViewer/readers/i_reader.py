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

import abc
import collections

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.MLogging import LOG


class InvalidFileError(Exception):
    """This class implements an exception for invalid file."""


class InvalidAtomError(Exception):
    """This class implements an exception raised in case of an invalid atom selection."""


class IReader(abc.ABC):
    """This class implements an interface for trajectory readers."""

    def __init__(self, filename):
        """Constructor.

        Args:
            filename (str): the trajectory filename
        """

        self._filename = filename

        self._n_frames = 0

        self._n_atoms = 0

    @property
    def filename(self):
        return self._filename

    @property
    def n_atoms(self):
        return self._n_atoms

    @property
    def atom_ids(self):
        return self._atom_ids

    @property
    def atom_names(self):
        return self._atom_names

    @property
    def atom_types(self):
        return self._atom_types

    @property
    def molecules(self):
        mol_indexes = collections.OrderedDict()

        for i, resid in enumerate(self._residue_ids):
            mol_indexes.setdefault(resid, []).append(i)

        return list(mol_indexes.values())

    @property
    def residue_ids(self):
        return self._residue_ids

    @property
    def residue_names(self):
        return self._residue_names

    @property
    def n_frames(self):
        return self._n_frames

    @property
    def times(self):
        return self._times

    @abc.abstractmethod
    def read_frame(self, frame):
        pass

    @abc.abstractmethod
    def read_pbc(self, frame):
        pass

    def get_atom_indexes(self, residue_names, atom_names):
        """Return the nested list of the indexes of the atoms whose residue and name are respectively in the provided
        list of residue and atom names.

        Args:
            residue_names (list of str): the residues to scan
            atom_names (list of str): the atoms to scan
        """

        indexes = []
        for i, at in enumerate(self._atom_names):
            current_residue = self._residue_names[i]
            if current_residue not in residue_names:
                continue

            if at in atom_names:
                indexes.append(i)

        indexes_per_molecule = collections.OrderedDict()
        for idx in indexes:
            resid = self._residue_ids[idx]
            indexes_per_molecule.setdefault(resid, []).append(idx)

        indexes_per_molecule = list(indexes_per_molecule.values())

        return indexes_per_molecule

    def guess_atom_types(self):
        """Guess the atom type (element) from their atom names.

        For standard residues, the strategy is to start from the left and search
        by increasing length until a valid element is found.
        For unknown residue, the strategy is opposite. Indeed, we start from the
        right and search by decreasing length until a valid element is found.
        The elemenents are searched in an internal YAML database.
        """

        # Retrieve all the chemical symbols from the internal database
        symbols = [at["symbol"].upper() for at in ATOMS_DATABASE]

        self._atom_types = []
        for i in range(self._n_atoms):
            atom_name = self._atom_names[i]

            # Remove the trailing and initial digits from the upperized atom names
            upper_atom_name = atom_name.upper()
            upper_atom_name = upper_atom_name.lstrip("0123456789").rstrip("0123456789")

            # Case of the an atom that belongs to a standard residue
            # Guess the atom type by the starting from the first alpha letter from the left,
            # increasing the word by one letter if there was no success in guessing the atom type

            start = len(upper_atom_name)
            while True:
                upper_atom_name = upper_atom_name[:start]
                if upper_atom_name in symbols:
                    self._atom_types.append(upper_atom_name.capitalize())
                    break
                if start == 0:
                    raise ValueError(f"Unknown atom type: {atom_name}")
                start -= 1

    def read_atom_trajectory(self, index):
        """Read the trajectory of a single atom with a given index

        Returns:
            3-tuple: the coordinates of the atoms through the trajectory alongside with the lower bounds and upper bounds
        """

        if index < 0 or index >= self._n_atoms:
            raise InvalidAtomError("Invalid atom index")

        return self._trajectory.read_atomic_trajectory(index)
