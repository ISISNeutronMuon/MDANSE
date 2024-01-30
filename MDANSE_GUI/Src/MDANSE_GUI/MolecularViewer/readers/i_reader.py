# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/pygenplot/__init__.py
# @brief     molecular viewer code from the "waterstay" project
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

import abc
import collections
import logging
import os

# import pandas as pd

import numpy as np

from MDANSE_GUI.MolecularViewer.database import (
    CHEMICAL_ELEMENTS,
    STANDARD_RESIDUES,
)

# from waterstay.extensions.atoms_in_shell import atoms_in_shell
# from waterstay.utils.progress_bar import progress_bar


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

        if not os.path.exists(filename):
            raise IOError("The file {} does not exist.".format(filename))

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
        symbols = [at["symbol"].upper() for at in CHEMICAL_ELEMENTS["atoms"].values()]

        self._atom_types = []
        for i in range(self._n_atoms):
            atom_name = self._atom_names[i]
            residue_name = self._residue_names[i]

            # Remove the trailing and initial digits from the upperized atom names
            upper_atom_name = atom_name.upper()
            upper_atom_name = upper_atom_name.lstrip("0123456789").rstrip("0123456789")

            # Case of the an atom that belongs to a standard residue
            # Guess the atom type by the starting from the first alpha letter from the left,
            # increasing the word by one letter if there was no success in guessing the atom type
            if residue_name in STANDARD_RESIDUES:
                start = 1
                while True:
                    upper_atom_name = upper_atom_name[:start]
                    if upper_atom_name in symbols:
                        self._atom_types.append(upper_atom_name.capitalize())
                        break
                    if start > len(atom_name):
                        raise ValueError("Unknown atom type: {}".format(atom_name))
                    start += 1
            # Case of the an atom that does not belong to a standard residue
            # Guess the atom type by the starting from whole atom name,
            # decreasing the word by one letter from the right if there was no success in guessing the atom type
            else:
                start = len(upper_atom_name)
                while True:
                    upper_atom_name = upper_atom_name[:start]
                    if upper_atom_name in symbols:
                        self._atom_types.append(upper_atom_name.capitalize())
                        break
                    if start == 0:
                        raise ValueError("Unknown atom type: {}".format(atom_name))
                    start -= 1

    def read_atom_trajectory(self, index):
        """Read the trajectory of a single atom with a given index

        Returns:
            3-tuple: the coordinates of the atoms through the trajectory alongside with the lower bounds and upper bounds
        """

        if index < 0 or index >= self._n_atoms:
            raise InvalidAtomError("Invalid atom index")

        coords = []
        lower_bounds = []
        upper_bounds = []
        for f in range(self._n_frames):
            frame = self.read_frame(f)
            coords.append(frame[index, :])
            lower_bounds.append(frame.min(axis=0))
            upper_bounds.append(frame.max(axis=0))

        coords = np.array(coords)
        lower_bounds = np.array(lower_bounds)
        upper_bounds = np.array(upper_bounds)

        return coords, lower_bounds, upper_bounds

    def residues_in_shell(
        self, residue_names, atom_names, center, radius, *, selected_frames=None
    ):
        """Compute the residence time of molecules of a given type which are within a shell around an atomic center.

        Args:
            residue_names (list of str): the residues to scan
            target_atoms (list of str): the atoms to scan
            center (int): the index of the atomic center
            radius (float): the radius to scan around the atomic center
        """

        if selected_frames is None:
            selected_frames = list(range(self._n_frames))

        # Retrieve the indexes of the atoms which belongs to each molecule of the selected type
        target_indexes = self.get_atom_indexes(residue_names, atom_names)
        if not target_indexes:
            logging.warning(
                "No atom found that matches {}@{}".format(atom_names, residue_names)
            )
            return None

        # Initialize the output array
        occupancies = np.zeros(
            (len(target_indexes), len(selected_frames)), dtype=np.int32
        )

        progress_bar.reset(len(selected_frames))

        # Loop over the frame of the trajectory
        for i, frame in enumerate(selected_frames):
            # Read the frame at time=frame
            coords = self.read_frame(frame)

            # Read the direct cell at time=frame
            cell = self.read_pbc(frame)

            # Compute the reverse cell at time=frame
            rcell = np.linalg.inv(cell)

            # Scan for the molecules of the selected type which are found around the atomic center by the selected radius
            atoms_in_shell(
                coords, cell, rcell, target_indexes, center, radius, occupancies[:, i]
            )

            progress_bar.update(i + 1)

        mol_ids = [self._residue_ids[v[0]] for v in target_indexes]

        selected_times = [self._times[f] for f in selected_frames]
        occupancies = pd.DataFrame(occupancies, index=mol_ids, columns=selected_times)

        return occupancies
