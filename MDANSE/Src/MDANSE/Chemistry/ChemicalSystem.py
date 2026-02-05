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
import itertools as it
from collections.abc import Iterable
from functools import reduce
from pathlib import Path
from typing import Any, SupportsInt

import h5py
import networkx as nx
import numpy as np
from more_itertools import padded
from rdkit import Chem
from rdkit.Chem import rdDetermineBonds
from rdkit.Geometry import Point3D

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Units import measure
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
        # rdkit DetermineBondOrders doesn't work with dummy atoms. we
        # avoid adding them to the rdkit_mol but will need to map from
        # the rdkit atom indexes to the ones in MDANSE
        self._rdkit_map = {}
        self._rdkit_map_inv = {}
        self._rdkit_dummy_atms = set()

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

        self._rdkit_dummy_atms = {
            atom.GetIdx()
            for atom in self.rdkit_mol.GetAtoms()
            if atom.GetAtomicNum() == 0
        }

    def add_atom(self, atm_num: int) -> int:
        rdkit_atm = Chem.Atom(atm_num) if atm_num is not None else Chem.Atom(0)
        rdkit_atm.SetNumExplicitHs(0)
        rdkit_atm.SetNoImplicit(True)
        return self.rdkit_mol.AddAtom(rdkit_atm)

    def add_bonds(self, pair_list: Iterable[tuple[SupportsInt, SupportsInt]]):
        self._bonds.extend(pair_list)
        for pair in pair_list:
            i, j = int(pair[0]), int(pair[1])
            if i not in self._rdkit_dummy_atms and j not in self._rdkit_dummy_atms:
                # Ignore the bonds to any dummy atoms. This means that
                # the SMARTS pattern match will ignore any bonds to
                # dummy atoms. E.g. [OX2] will match oxygen atoms connected
                # to two other real atoms even if it is also connected to
                # dummy atoms.
                self.rdkit_mol.AddBond(i, j, Chem.rdchem.BondType.UNSPECIFIED)

    def set_bond_orders(
        self, coords: np.ndarray, *, max_iters: int = 1000, max_natms: int = 100
    ):
        """Set the bond types for the bonds in the rdkit_mol.

        Parameters
        ----------
        coords : np.ndarray
            The coordinates of the system to determine the bond types
            from.
        max_iters: int
            The maximum number of iterations used in the rdkit
            DetermineBondOrders function.
        max_natms : int
            Skips DetermineBondOrders for molecules with a number of atoms
            larger than max_natms.
        """

        uniq_submols = {}
        coord_ang = coords * measure(1.0, "nm").toval("ang")

        # Calling rdDetermineBonds.DetermineBondOrders for a large system
        # is quite computationally expensive. It's better to call this
        # function for unique molecules and then copy over all the bond
        # types for all others. We also need to remove dummy atom before
        # using rdDetermineBonds.DetermineBondOrders because it can't
        # deal with them.
        for cluster_name in self._clusters:
            for idx, cluster in enumerate(self._clusters[cluster_name]):
                cluster_no_dummies = [
                    i for i in cluster if i not in self._rdkit_dummy_atms
                ]

                if len(cluster_no_dummies) > max_natms:
                    LOG.warning(
                        f"Number of atoms in {cluster_name} with idx {idx} "
                        f"is very large - skipping bond type determination. "
                        f"SMARTS pattern matching will not work as expected. "
                        f"Bond types set to UNSPECIFIED, use the bond type wildcard "
                        f"~ to match bonds in this molecule and use general atom symbols "
                        f"e.g. [#6] instead of [C] or [c]. See "
                        f"https://www.daylight.com/dayhtml/doc/theory/theory.smarts.html "
                        f"for more details on SMARTS pattern matching."
                    )
                    continue

                mapping = {}

                submolecule = Chem.RWMol()
                for i in cluster_no_dummies:
                    new_idx = submolecule.AddAtom(self.rdkit_mol.GetAtomWithIdx(i))
                    mapping[i] = new_idx
                bond_idxs = []
                for i, j in it.combinations(cluster_no_dummies, 2):
                    bond = self.rdkit_mol.GetBondBetweenAtoms(i, j)
                    if bond is None:
                        continue
                    k = bond.GetBeginAtomIdx()
                    m = bond.GetEndAtomIdx()
                    submolecule.AddBond(
                        mapping[k], mapping[m], Chem.rdchem.BondType.UNSPECIFIED
                    )
                    bond_idxs.append(bond.GetIdx())

                # canonical=False should deal molecules in the same
                # cluster_name group which do not have the same atom ordering
                smiles = Chem.MolToSmiles(submolecule, canonical=False)

                if smiles in uniq_submols:
                    submolecule = uniq_submols[smiles]
                else:
                    conf = Chem.Conformer(len(cluster_no_dummies))
                    for i, j in enumerate(cluster_no_dummies):
                        if j not in self._rdkit_dummy_atms:
                            x, y, z = coord_ang[j]
                            conf.SetAtomPosition(i, Point3D(x, y, z))
                    submolecule.AddConformer(conf)
                    try:
                        LOG.info(
                            f"Determining bond orders for molecule "
                            f"{cluster_name} with index {idx}"
                        )
                        rdDetermineBonds.DetermineBondOrders(
                            submolecule,
                            charge=0,
                            maxIterations=max_iters,
                        )
                    except Exception as e:
                        LOG.error(
                            f"Error determining bond orders for molecule "
                            f"{cluster_name} with index {idx}: {e}. SMARTS "
                            f"pattern matching will not work as expected. Bond "
                            f"types set to UNSPECIFIED use bond type wildcard "
                            f"~ to match bonds in this molecule."
                        )
                    uniq_submols[smiles] = submolecule

                for i, j in enumerate(bond_idxs):
                    submol_bond = submolecule.GetBondWithIdx(i)
                    mol_bond = self.rdkit_mol.GetBondWithIdx(j)
                    bond_type = submol_bond.GetBondType()
                    mol_bond.SetBondType(bond_type)
                    if bond_type == Chem.rdchem.BondType.AROMATIC:
                        mol_bond.GetBeginAtom().SetIsAromatic(True)
                        mol_bond.GetEndAtom().SetIsAromatic(True)

        # determine ring info for the rdkit_mol so the SMART pattern like
        # [cR1] can be used
        Chem.GetSymmSSSR(self.rdkit_mol)

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
                f"{atom}{count}"
                for atom, count in zip(unique_atoms, counts, strict=True)
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
        try:
            matches = self.rdkit_mol.GetSubstructMatches(
                Chem.MolFromSmarts(smarts), maxMatches=maxmatches
            )
        except RuntimeError as e:
            LOG.error(f"Unable to run pattern match using {smarts}: {e}")
            return set()
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
        for key, vals in self._clusters.items():
            # unable to store array with inhomogeneous row lengths
            # we will pad them with -1, we will ignore these values
            # when the trajectory get loaded up see self.load
            size = max(len(val) for val in vals)
            new_vals = [list(padded(val, fillvalue=-1, n=size)) for val in vals]
            clusters_group.create_dataset(key, data=new_vals)

    def load(self, trajectory: h5py.File | Path | str):
        """Read the ChemicalSystem information from the trajectory.

        Parameters
        ----------
        trajectory : str | h5py.File
            Filename or a file object of the trajectory.
        """
        close_on_end = False
        if isinstance(trajectory, Path | str):
            close_on_end = True
            source = h5py.File(trajectory)
        else:
            source = trajectory

        assert isinstance(source, h5py.File | dict)

        if "composition" not in source:
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
                [int(x) for x in line if int(x) >= 0]
                for line in grp[f"clusters/{cluster}"]
            ]
        if close_on_end:
            source.close()

    def legacy_load(self, trajectory: h5py.File | Path | str):
        """Read the ChemicalSystem from an old (pre-2025) trajectory.
        Parameters
        ----------
        trajectory : Path | str | h5py.File
            Filename or a file object of the trajectory.
        """

        close_on_end = False
        if isinstance(trajectory, (Path, str)):
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
