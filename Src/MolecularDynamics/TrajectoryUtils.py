# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/MolecularDynamics/Trajectory.py
# @brief     Implements module/class/test Trajectory
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import operator
from typing import Union

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, AtomGroup, ChemicalSystem, _ChemicalEntity
from MDANSE.Extensions import fast_calculation


class MolecularDynamicsError(Error):
    pass


class UniverseAdapterError(Error):
    pass


def atom_index_to_molecule_index(chemical_system: ChemicalSystem) -> dict[int, int]:
    """
    Maps the indices of all atoms in a chemical system to the indices of their root parent chemical entities and returns
    the lookup table. This can then be used to retrieve the root parent chemical entity of an atom through the
    chemical_entities property of ChemicalSystem.

    :param chemical_system: the chemical system whose lookup table is to be generated
    :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

    :return: a lookup table mapping atom indices to the indices of their root chemical entity
    :rtype: dict
    """

    lut = {}
    for i, ce in enumerate(chemical_system.chemical_entities):
        for at in ce.atom_list():
            lut[at.index] = i

    return lut


def brute_formula(chemical_entity: _ChemicalEntity, sep: str = '_', ignore_ones: bool = False) -> str:
    """
    Determine the molecular formula of a given chemical entity.

    :param chemical_entity: the chemical entity whose formula is to be deternimed
    :type chemical_entity: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalEntity`

    :param sep: the separator used between elements, i.e. with the default separator a water molecule will return H2_O1
    :type sep: str

    :param ignore_ones: determines whether number 1 should be printed, i.e. whether water should be H2_O1 or H2_O
    :type ignore_ones: bool

    :return: the molecular formula
    :rtype: str
    """

    contents = {}

    for at in chemical_entity.atom_list():
        contents[at.symbol] = str(int(contents.get(at.symbol, 0)) + 1)

    formula = sep.join([''.join(v) for v in sorted(contents.items())])

    if ignore_ones:
        return formula.replace('1', '')
    else:
        return formula


def build_connectivity(chemical_system: ChemicalSystem, tolerance: float = 0.05) -> None:
    """
    Creates bonds between atoms within each atom cluster as well as between loose atoms. Bonds are created only between
    atoms whose covalent radii overlap, i.e. for whose the sum of their covalent radii plus the tolerance is smaller
    than their distance. Bonds are created only between atoms within a
    :class: `MDANSE.Chemistry.ChemicalEntity.AtomCluster` or between loose atoms (atoms that are not part of another
    chemical entity or which are the only atom in their chemical entity). No bonds are created between atoms of other
    chemical entities (unless it's the only atom in it), and no bonds are created between atoms in different atom
    clusters or between atoms in an entity and loose atoms, regardless of their positions.

    Please note that the coordinates of atoms are taken from the configuration registered in the provided chemical
    system.

    :param chemical_system: the chemical system in which bonds are to be created
    :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

    :param tolerance: the tolerance used for defining whether two atoms are bonded in nm
    :type tolerance: float

    :return: None
    """

    conf = chemical_system.configuration

    atom_clusters = []
    single_atoms_objects = []

    # Find all atom clusters, loose atoms, and one-atom objects
    for ce in chemical_system.chemical_entities:
        if isinstance(ce, Atom):
            single_atoms_objects.append(ce)
        elif isinstance(ce, AtomCluster):
            atom_clusters.append(ce)
        else:
            if ce.number_of_atoms() == 1:
                single_atoms_objects.extend(ce.atom_list())

    if single_atoms_objects:
        atom_clusters.append(AtomCluster('', single_atoms_objects, parentless=True))

    for ce in atom_clusters:

        atoms = sorted(ce.atom_list(), key=operator.attrgetter('index'))

        n_atoms = len(atoms)
        indexes = [at.index for at in atoms]
        coords = conf.variables['coordinates'][indexes, :]
        cov_radii = np.zeros((n_atoms,), dtype=np.float64)
        for i, at in enumerate(atoms):
            cov_radii[i] = ATOMS_DATABASE[at.symbol.capitalize()]['covalent_radius']

        bonds = fast_calculation.cpt_cluster_connectivity_nopbc(coords, cov_radii, tolerance)

        for idx1, idx2 in bonds:
            atoms[idx1].bonds.append(atoms[idx2])
            atoms[idx2].bonds.append(atoms[idx1])


def find_atoms_in_molecule(chemical_system: ChemicalSystem, entity_name: str, atom_names: list[str],
                           indexes: bool = False) -> list[list[Union[Atom, int]]]:
    """
    Finds all chemical entities of the provided name within the chemical system, and then retrieves all atoms from each
    of the found entities whose name matches one of the provided atom names. However, please note that only the chemical
    entities directly registered in the chemical system are searched, i.e. the chemical_entities property of
    :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`. Therefore, for example, if a chemical system consists of a
    Protein with name 'protein' which consists of 2 NucleotideChains 'chain1' and 'chain2', and this function is called
    with the entity_name parameter set to 'chain1', an empty list will be returned.

    :param chemical_system: the chemical system to be searched
    :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

    :param entity_name: the name of the chemical entity to match
    :type entity_name: str

    :param atom_names: the list of atom names to search
    :type atom_names: list

    :param indexes: if True the indexes of the atoms will be returned otherwise the Atom instances will be returned
    :type indexes: bool

    :return: the list of indexes or atom instances found
    :rtype: list
    """

    # Loop over the chemical entities of the chemical entity and keep only those whose name match |ce_name|
    chemical_entities = []
    for ce in chemical_system.chemical_entities:
        if ce.name == entity_name:
            chemical_entities.append(ce)

    match = []
    for ce in chemical_entities:
        atoms = ce.atom_list()
        names = [at.name for at in atoms]
        try:
            match.append([atoms[names.index(at_name)] for at_name in atom_names])
        except ValueError:
            match.append([])

    if indexes is True:
        match = [[at.index for at in at_list] for at_list in match]

    return match


def get_chemical_objects_dict(chemical_system: ChemicalSystem) -> dict[str, list[_ChemicalEntity]]:
    """
    Maps all chemical entities in a chemical system to their names, and returns this as a dict. Please note that only
    the top level chemical entities (those directly registered in chemical system) are mapped; children entities are not
    mapped. Therefore, if a chemical system containing a protein called 'protein' which itself consists of nucleotide
    chains 'chain1' and 'chain2' is passed in to this function, the following dict would be returned {'protein': [
    Protein]}.

    :param chemical_system: the chemical system whose entities are to be retrieved
    :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

    :return: a dict mapping the names of the entities in a chemical system to a list of entities with that name
    :rtype: dict
    """

    d = {}
    for ce in chemical_system.chemical_entities:
        d.setdefault(ce.name, []).append(ce)

    return d


def group_atoms(chemical_system: ChemicalSystem, groups: list[list[int]]) -> list[AtomGroup]:
    """
    Groups select atoms into :class: `MDANSE.Chemistry.ChemicalEntity.AtomGroup` objects according to the instructions
    in the 'groups' argument. Please note, however, that the groups are created strictly according to this parameter,
    meaning that not all atoms are necessarily placed into a group and that some atoms may be placed into multiple
    groups, depending on the instructions. The only exception to this is if one of the lists in the 'groups' parameters
    is empty, in which case no group is created for that list, the instruction silently ignored.

    :param chemical_system: the chemical system whose atoms are to be grouped
    :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

    :param groups: the nested list of indexes, each sublist defining a group
    :type groups: list

    :return: list of atom groups as specified
    :rtype: list
    """
    atoms = chemical_system.atom_list()

    groups = [AtomGroup([atoms[index] for index in gr]) for gr in groups if gr]

    return groups


def resolve_undefined_molecules_name(chemical_system: ChemicalSystem) -> None:
    """
    Changes the names of all top-level chemical entities (those directly registered with a chemical system) that have no
    name to their molecular formulae. To be considered to have no name, the molecule's name must be an empty string or a
    string that consists of only spaces. The molecular formula is determined through
    :func: `MDANSE.MolecularDynamics.TrajectoryUtils.resolve_undefined_molecules_name`.

    :param chemical_system: the chemical system
    :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

    :return: None
    """
    # Is it okay to not do this for children?
    for ce in chemical_system.chemical_entities:
        if not ce.name.strip():
            ce.name = brute_formula(ce, sep="")


def sorted_atoms(atoms: list[Atom], attribute: str = None) -> list[Union[Atom, float, int, str, list]]:
    """
    Sort a list of atoms according to their index, and returns either the sorted list of atoms or the values of the
    specified attribute.

    :param atoms: the atom list to be sorted
    :type atoms: list

    :param attribute: if not None, return the attribute of the atom instead of the atom instance
    :type attribute: str

    :return: the sorted atoms or the value of their specified attributes
    :rtype: list
    """

    atoms = sorted(atoms, key=operator.attrgetter('index'))

    if attribute is None:
        return atoms
    else:
        return [getattr(at, attribute) for at in atoms]
