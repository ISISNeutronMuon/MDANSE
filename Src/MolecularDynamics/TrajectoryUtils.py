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

from MMTK.Collections import Collection
from MMTK.Trajectory import Trajectory

from MDANSE.Core.Error import Error
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster
from MDANSE.Extensions import fast_calculation

class MolecularDynamicsError(Error):
    pass

class UniverseAdapterError(Error):
    pass

def atomindex_to_moleculeindex(universe):
    
    d = {}
    for i,obj in enumerate(universe.objectList()):
        for at in obj.atomList():
            d[at.index] = i
                
    return d
    
def brute_formula(molecule, sep='_'):
    
    contents = {}
    
    for at in molecule.atom_list():
        contents[at.symbol] = str(int(contents.get(at.symbol,0)) + 1)
    
    return sep.join([''.join(v) for v in sorted(contents.items())])

def build_connectivity(chemicalSystem ,tolerance=0.05, unit_cell=None):

    bonds = []
    
    conf = chemicalSystem.configuration
    conf = conf.contiguous_configuration()

    scannedObjects = [ce for ce in chemicalSystem.chemical_entities if isinstance(ce,AtomCluster)]

    singleAtomsObjects = []
    for ce in chemicalSystem.chemical_entities:
        if isinstance(ce,Atom):
            singleAtomsObjects.append(ce)
        else:
            if ce.number_of_atoms() == 1:
                singleAtomsObjects.extend(ce.atom_list())

    if singleAtomsObjects:
        scannedObjects.append(AtomCluster('',singleAtomsObjects))
                
    for ce in scannedObjects:
                                                        
        atoms = sorted(ce.atom_list(), key = operator.attrgetter('index'))
        nAtoms = len(atoms)
        indexes = [at.index for at in atoms]
        coords = conf.variables['coordinates'][indexes,:]
        covRadii = np.zeros((nAtoms,), dtype=np.float64)
        for i,at in enumerate(atoms):
            covRadii[i] = ATOMS_DATABASE[at.symbol.capitalize()]['covalent_radius']
        
        if unit_cell is None :
            fast_calculation.cpt_cluster_connectivity_nopbc(coords,covRadii,tolerance,bonds)
        else:
            inverse_unit_cell = np.linalg.inv(unit_cell)
            fast_calculation.cpt_cluster_connectivity_pbc(coords,unit_cell.T, inverse_unit_cell.T, covRadii,tolerance,bonds)
                  
        for idx1,idx2 in bonds:
            atoms[idx1].bonds.append(atoms[idx2])                  
            atoms[idx2].bonds.append(atoms[idx1])

def find_atoms_in_molecule(universe, moleculeName, atomNames, indexes=False):

    molecules = []
    for obj in universe.objectList():
        if obj.name == moleculeName:
            molecules.append(obj)
                    
    match = []
    for mol in molecules:
        atoms = mol.atomList()
        names = [at.name for at in mol.atomList()]
        l = [atoms[names.index(atName)] for atName in atomNames]

        match.append(l)
        
    if indexes is True:
        match = [[at.index for at in atList] for atList in match]
        
    return match

def get_chemical_objects_size(universe):
    
    d = {}
    for obj in universe.objectList():
        if d.has_key(obj.name):
            continue
        d[obj.name] = obj.numberOfAtoms()
        
    return d

def get_chemical_objects_dict(universe):
    
    d = {}
    for obj in universe.objectList():
        d.setdefault(obj.name, []).append(obj)
        
    return d
        
def get_chemical_objects_number(universe):
    
    d = {}
    for obj in universe.objectList():
        if d.has_key(obj.name):
            d[obj.name] += 1
        else:
            d[obj.name] = 1
        
    return d
                                                                    
def partition_universe(universe,groups):
    
    atoms = sorted(universe.atomList(), key = operator.attrgetter('index'))
                                        
    coll = [Collection([atoms[index] for index in gr]) for gr in groups]
    
    return coll

def read_atoms_trajectory(trajectory, atoms, first, last=None, step=1, variable="configuration", weights=None, dtype=np.float64):
    
    if not isinstance(atoms,(list,tuple)):
        atoms = [atoms]
        
    if last is None:
        last = len(trajectory)
        
    nFrames = len(range(first, last, step))
    
    serie = np.zeros((nFrames,3), dtype=dtype)
    
    if weights is None or len(atoms) == 1:
        weights = [1.0]*len(atoms)

    for i,at in enumerate(atoms):
        w = weights[i]
        serie += w*trajectory.readParticleTrajectory(at, first, last, step, variable).array
                
    serie /= sum(weights)
    
    return serie

def resolve_undefined_molecules_name(chemicalSystem):
    
    for ce in chemicalSystem.chemical_entities:
        if not ce.name.strip():
            ce.name = brute_formula(ce,sep="")

def sorted_atoms(chemicalSystem,attribute=None):

    atoms = sorted(chemicalSystem.atom_list(), key = operator.attrgetter('index'))
    
    if attribute is None:
        return atoms
    else:
        return [getattr(at,attribute) for at in atoms]
    
class MMTKTrajectory(Trajectory):
    
    def __init__(self,*args,**kwargs):
        
        Trajectory.__init__(self,*args,**kwargs)
        
        resolve_undefined_molecules_name(self.universe)
         
        build_connectivity(self.universe)
