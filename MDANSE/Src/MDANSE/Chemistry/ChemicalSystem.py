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

import copy
from collections.abc import Iterable
from functools import reduce
from typing import Any, SupportsInt

import h5py
import networkx as nx
import numpy as np
from rdkit import Chem

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.MLogging import LOG


class ChemicalSystem:
    """Stores the contents and topology of a trajectory."""

    def __init__(self, name: str = "", trajectory=None):
        """Populate the arrays with values from the trajectory.

        Parameters
        ----------
        name : str, optional
            text label of this system
        trajectory : Trajectory, optional
            instance of the Trajectory class, by default None
        """
        self.name = str(name)
        self._database = ATOMS_DATABASE
        if trajectory is not None:
            self._database = trajectory

        self._total_number_of_atoms = 0
        self._atom_types = []
        self._atom_names = None
        self._atom_indices = []
        self._labels = {}  # arbitrary tag attached to atoms (e.g. residue name)

        self._bonds = []

        self._clusters = {}

        self.rdkit_mol = Chem.RWMol()
        self._unique_elements = set()

    def __str__(self):
        return (
            f"ChemicalSystem {self.name} consisting of {len(self._atom_types)}"
            " atoms in {len(self._clusters)} molecules"
        )

    def initialise_atoms(
        self,
        element_list: list[str],
        name_list: list[str] | None = None,
    ):
        """Assign indices to atoms, save their types and names.

        Parameters
        ----------
        element_list : list[str]
            list of chemical element labels
        name_list : Optional[list[str]], optional
            list of atom text labels from trajectory, by default None

        """
        self._atom_indices = [
            self.add_atom(self._database.get_atom_property(symbol, "atomic_number"))
            for symbol in element_list
        ]
        self._atom_types = [str(x) for x in element_list]
        self._total_number_of_atoms = len(self._atom_indices)
        self._unique_elements.update(set(element_list))
        if name_list is not None:
            self._atom_names = [str(x) for x in name_list]

    def add_atom(self, atm_num: int) -> int:
        rdkit_atm = Chem.Atom(atm_num) if atm_num is not None else Chem.Atom(0)
        rdkit_atm.SetNumExplicitHs(0)
        rdkit_atm.SetNoImplicit(True)
        return self.rdkit_mol.AddAtom(rdkit_atm)

    def add_bonds(self, pair_list: Iterable[tuple[SupportsInt, SupportsInt]]):
        self._bonds.extend(pair_list)
        for pair in pair_list:
            self.rdkit_mol.AddBond(
                int(pair[0]), int(pair[1]), Chem.rdchem.BondType.UNSPECIFIED
            )

    def add_labels(self, label_dict: dict[str, list[int]]):
        for key, item in label_dict.items():
            self._labels[key] = self._labels.get(key, []) + item

    @staticmethod
    def _rename_isotopes(element: str):
        if element[-1].isdigit():
            return f"[{element}]"
        return element

    def add_clusters(self, group_list: list[list[int]]):
        for group in group_list:
            sorted_group = sorted(set(group))

            if len(sorted_group) < 2:
                continue

            atom_list = [self._atom_types[index] for index in group]
            unique_atoms, counts = np.unique(atom_list, return_counts=True)
            unique_atoms = map(self._rename_isotopes, unique_atoms)
            name = "_".join(
                f"{atom}{count}" for atom, count in zip(unique_atoms, counts)
            )

            if name not in self._clusters:
                self._clusters[name] = [sorted_group]
            elif sorted_group not in self._clusters[name]:
                self._clusters[name].append(group)

    def has_substructure_match(self, smarts: str) -> bool:
        """Check if there is a substructure match.

        Parameters
        ----------
        smarts : str
            SMARTS string.

        Returns
        -------
        bool
            True if the there is a substructure match.

        """
        return self.rdkit_mol.HasSubstructMatch(Chem.MolFromSmarts(smarts))

    def get_substructure_matches(
        self,
        smarts: str,
        maxmatches: int = 1000000,
    ) -> set[int]:
        """Get the indices which match the smarts string. Note that
        the default bond type in MDANSE is
        Chem.rdchem.BondType.UNSPECIFIED.

        Parameters
        ----------
        smarts : str
            SMARTS string.
        maxmatches : int
            Maximum number of matches used in the GetSubstructMatches
            rdkit method.

        Returns
        -------
        set[int]
            An set of matched atom indices.
        """
        matches = self.rdkit_mol.GetSubstructMatches(
            Chem.MolFromSmarts(smarts), maxMatches=maxmatches
        )
        return {ind for match in matches for ind in match}

    @property
    def atom_list(self) -> list[str]:
        """Return the types of all atoms in the ChemicalSystem."""
        return self._atom_types

    @property
    def name_list(self) -> list[str]:
        """Return the names of all atoms in the ChemicalSystem."""
        if self._atom_names is not None:
            return self._atom_names
        return self._atom_types

    def atom_property(self, atom_property: str) -> list[Any]:
        """Return the values of a specific property, for all atoms in the system."""
        lookup = {}
        for atom in self._unique_elements:
            lookup[atom] = self._database.get_atom_property(atom, atom_property)
        return [lookup[atom] for atom in self.atom_list]

    def grouping_level(self, index: int) -> int:
        """Temporarily, there is no grouping test.

        Parameters
        ----------
        index : int
            atom index

        Returns
        -------
        int
            grouping level for the GroupingLevelConfigurator

        """
        return 0

    def copy(self) -> ChemicalSystem:
        """Return a new instance of ChemicalSystem with the same contents.

        Returns
        -------
        ChemicalSystem
            A copy of the existing ChemicalSystem.

        """
        cs = ChemicalSystem(self.name)

        for attribute_name, attribute_value in self.__dict__.items():
            if attribute_name in ["rdkit_mol", "_configuration"]:
                continue
            setattr(cs, attribute_name, copy.deepcopy(attribute_value))

        return cs

    def find_clusters_from_bonds(self):
        """Build cluster information based on the saved chemical bonds.

        Builds graphs and walks them to identify all the atoms that can
        be reached from a starting atom by following bonds.
        """
        molecules = []
        atom_pool = list(self._atom_indices)

        total_graph = nx.Graph()
        total_graph.add_nodes_from(atom_pool)
        total_graph.add_edges_from(self._bonds)
        while len(atom_pool) > 0:
            last_atom = atom_pool.pop()
            temp_dict = nx.dfs_successors(total_graph, last_atom)
            others = reduce(list.__add__, temp_dict.values(), [])
            for atom in others:
                atom_pool.remove(atom)
            molecule = [last_atom, *others]
            molecules.append(sorted(molecule))
        self.add_clusters(molecules)

    def unique_molecules(self) -> list[str]:
        """Return the list of unique names in the chemical system."""
        return [str(x) for x in self._clusters]

    def number_of_molecules(self, molecule_name: str) -> int:
        """Return the number of molecules with the given name in the system."""
        return len(self._clusters[molecule_name])

    @property
    def number_of_atoms(self) -> int:
        """The number of non-ghost atoms in the ChemicalSystem."""
        return self._total_number_of_atoms

    @property
    def all_indices(self) -> set[int]:
        """The number of non-ghost atoms in the ChemicalSystem."""
        return set(self._atom_indices)

    @property
    def total_number_of_atoms(self) -> int:
        """The number of all atoms in the ChemicalSystem, including ghost ones."""
        return self._total_number_of_atoms

    def serialize(self, h5_file: h5py.File) -> None:
        """Write the current system information into the HDF5 file.

        Parameters
        ----------
        h5_file : h5py.File
            File object of the target trajectory, open for writing.

        """
        string_dt = h5py.special_dtype(vlen=str)

        grp = h5_file.create_group("/composition")
        grp.attrs["name"] = self.name

        try:
            grp.create_dataset("atom_types", data=self._atom_types, dtype=string_dt)
        except TypeError:
            LOG.error(f"Bad array: {self._atom_types}")
            import sys

            sys.exit(1)
        if self._atom_names is not None:
            try:
                grp.create_dataset("atom_names", data=self._atom_names, dtype=string_dt)
            except TypeError:
                LOG.error(f"Bad array: {self._atom_names}")
                import sys

                sys.exit(1)
        grp.create_dataset("atom_indices", data=self._atom_indices)

        grp.create_dataset("bonds", data=np.array(self._bonds))

        label_group = grp.create_group("labels")
        for key, value in self._labels.items():
            label_group.create_dataset(key, data=value)
        clusters_group = grp.create_group("clusters")
        for key, value in self._clusters.items():
            clusters_group.create_dataset(key, data=value)

    def load(self, trajectory: h5py.File | str):
        """Read the ChemicalSystem information from the trajectory.

        Parameters
        ----------
        trajectory : str | h5py.File
            Filename or a file object of the trajectory.
        """
        close_on_end = False
        if isinstance(trajectory, str):
            close_on_end = True
            source = h5py.File(trajectory)
        else:
            source = trajectory

        assert isinstance(source, (h5py.File, dict))

        if "composition" not in source.keys():
            if close_on_end:
                source.close()
            self.legacy_load(trajectory)
            return

        self.rdkit_mol = Chem.RWMol()

        grp = source["/composition"]
        self.name = grp.attrs["name"]

        atom_types = [binary.decode("utf-8") for binary in grp["atom_types"][:]]
        atom_names = None
        if "atom_names" in grp:
            atom_names = [binary.decode("utf-8") for binary in grp["atom_names"][:]]
        self.initialise_atoms(atom_types, atom_names)
        old_indices = [int(tag) for tag in grp["atom_indices"][:]]
        if not np.allclose(old_indices, self._atom_indices):
            LOG.error("Atoms got re-indexed on loading the trajectory")

        self.add_bonds([[int(pair[0]), int(pair[1])] for pair in grp["bonds"][:]])

        self._labels = {
            label: [int(tag) for tag in grp[f"labels/{label}"]]
            for label in map(str, grp["labels"])
        }

        for cluster in grp["clusters"]:
            self._clusters[str(cluster)] = [
                [int(x) for x in line] for line in grp[f"clusters/{cluster}"]
            ]
        if close_on_end:
            source.close()

    def legacy_load(self, trajectory: h5py.File | str):
        """Read the ChemicalSystem from an old (pre-2025) trajectory.
        Parameters
        ----------
        trajectory : str | h5py.File
            Filename or a file object of the trajectory.
        """

        close_on_end = False
        if isinstance(trajectory, str):
            close_on_end = True
            source = h5py.File(trajectory)
        else:
            source = trajectory

        self.rdkit_mol = Chem.RWMol()

        grp = source["/chemical_system"]
        self.name = grp.attrs["name"]
        atoms = grp["atoms"]
        element_list = [line[0].decode("utf-8").strip("'") for line in atoms]
        self.initialise_atoms(element_list)

        bonds = grp["bonds"]
        bond_list = bonds[:]
        self.add_bonds([[int(pair[0]), int(pair[1])] for pair in bond_list])

        if "atom_clusters" in grp:
            cluster_list = []
            for line in grp["atom_clusters"]:
                indices_string = line[0].decode("utf-8")
                indices_list = [int(x) for x in indices_string.strip("[]").split(",")]
                if indices_list:
                    cluster_list.append(indices_list)
            if cluster_list:
                self.add_clusters(cluster_list)
        if close_on_end:
            source.close()

        self.find_clusters_from_bonds()
