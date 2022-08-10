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

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, AtomGroup, ChemicalSystem, _ChemicalEntity
from MDANSE.Extensions import fast_calculation

class MolecularDynamicsError(Error):
    pass

class UniverseAdapterError(Error):
    pass


def atomindex_to_moleculeindex(chemicalSystem: ChemicalSystem):
    """Returns a lookup between the index of the atoms of a chemical system and the index 
    of their corresponding chemical entity.

    Args:
        chemicalSystem (MDANSE.Chemistry.ChemicalEntitiy.ChemicalSystem): the chemical system

    Returns:
        dict: the lookup table        
    """
    
    lut = {}
    for i,ce in enumerate(chemicalSystem.chemical_entities):
        for at in ce.atom_list:
            lut[at.index] = i
                
    return lut


def brute_formula(chemicalEntity: _ChemicalEntity, sep='_'):
    """Define the brute formula of a given chemical entity.

    Args:
        chemicalEntity (MDANSE.Chemistry.ChemicalEntity.ChemicalEntity): the chemical entity
        sep (str): the separator

    Returns:
        the brute formula
    """
    
    contents = {}
    
    for at in chemicalEntity.atom_list:
        contents[at.symbol] = str(int(contents.get(at.symbol,0)) + 1)
    
    return sep.join([''.join(v) for v in sorted(contents.items())])


def build_connectivity(chemicalSystem: ChemicalSystem ,tolerance=0.05):
    """Build the connectivity of the AtomCluster of a given chemical system.

    Args:
        chemicalSystem (MDANSE.Chemistry.ChemicalEntitiy.ChemicalSystem): the chemical system
        tolerance (float): the tolerance used for defining whether two atoms are bonded
    """

    bonds = []
    
    conf = chemicalSystem.configuration

    scannedObjects = [ce for ce in chemicalSystem.chemical_entities if isinstance(ce,AtomCluster)]
                
    singleAtomsObjects = []
    for ce in chemicalSystem.chemical_entities:
        if isinstance(ce,Atom):
            singleAtomsObjects.append(ce)
        else:
            if ce.number_of_atoms() == 1:
                singleAtomsObjects.extend(ce.atom_list)

    if singleAtomsObjects:
        scannedObjects.append(AtomCluster('',singleAtomsObjects, parentless=True))

    for ce in scannedObjects:

        atoms = sorted(ce.atom_list, key = operator.attrgetter('index'))

        nAtoms = len(atoms)
        indexes = [at.index for at in atoms]
        coords = conf.variables['coordinates'][indexes,:]
        covRadii = np.zeros((nAtoms,), dtype=np.float64)
        for i,at in enumerate(atoms):
            covRadii[i] = ATOMS_DATABASE[at.symbol.capitalize()]['covalent_radius']
        
        fast_calculation.cpt_cluster_connectivity_nopbc(coords,covRadii,tolerance,bonds)
                  
        for idx1,idx2 in bonds:
            atoms[idx1].bonds.append(atoms[idx2])                  
            atoms[idx2].bonds.append(atoms[idx1])


def find_atoms_in_molecule(chemicalSystem: ChemicalSystem, ceName, atomNames, indexes=False):
    """Find the atoms of a chemical system whose chemical entity match a given value 
    and atom names are within a given list.

    Args:
        chemicalSystem (MDANSE.Chemistry.ChemicalEntitiy.ChemicalSystem): the chemical system
        ceName (str): the name of the chemical entity to match
        atomNames (list): the list of atom names to search
        indexes (bool): if True the indexes of the atoms will be returned otherwise the Atom instances will be returned

    Returns:
        list: the list of indexes or atom instances found
    """

    # Loop over the chemical entities of the chemical entity and keep only those
    # whose name match |ce_name|
    chemicalEntities = []
    for ce in chemicalSystem.chemical_entities:
        if ce.name == ceName:
            chemicalEntities.append(ce)
                    
    match = []
    for ce in chemicalEntities:
        atoms = ce.atom_list
        names = [at.name for at in atoms]
        l = [atoms[names.index(at_name)] for at_name in atomNames]

        match.append(l)
        
    if indexes is True:
        match = [[at.index for at in atList] for atList in match]
        
    return match


def get_chemical_objects_dict(chemical_system: ChemicalSystem):
    """Return a dict of the chemical entities found in a chemical system.

    Args:
        chemicalSystem (MDANSE.Chemistry.ChemicalEntitiy.ChemicalSystem): the chemical system

    Returns:
        dict: a dict whose key and value are respectively the name and the instance of the
    chemical entities defined in the chemical system
    """
    
    d = {}
    for ce in chemical_system.chemical_entities:
        d.setdefault(ce.name, []).append(ce)
        
    return d


def group_atoms(chemicalSystem: ChemicalSystem,groups):
    """Group the atoms of a chemical system.

    Args:
        chemicalSystem (MDANSE.Chemistry.ChemicalEntitiy.ChemicalSystem): the chemical system
        groups (list): the nested list of indexes, each sublist defining a group

    Returns:
        list: the list of AtomGroup
    """
    
    atoms = sorted(chemicalSystem.atom_list, key=operator.attrgetter('index'))
                                        
    groups = [AtomGroup([atoms[index] for index in gr]) for gr in groups]

    return groups


def resolve_undefined_molecules_name(chemicalSystem: ChemicalSystem):
    """Resolve the name of the chemical entities with no names by using their
    brute formula.

    Args:
        chemicalSystem (MDANSE.Chemistry.ChemicalEntitiy.ChemicalSystem): the chemical system
    """
    
    for ce in chemicalSystem.chemical_entities:
        if not ce.name.strip():
            ce.name = brute_formula(ce,sep="")


def sorted_atoms(atoms: list[Atom], attribute=None):
    """Sort a list of atoms according.

    Args:
        atoms (list): the atom list
        attribute (str): if not None, return the attribute of the atom instead of the atom instance

    Returns:
        list: the sorted atoms
    """

    atoms = sorted(atoms, key=operator.attrgetter('index'))
    
    if attribute is None:
        return atoms
    else:
        return [getattr(at,attribute) for at in atoms]
    