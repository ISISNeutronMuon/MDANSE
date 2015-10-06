import operator

import numpy

from MMTK import Atom, AtomCluster
from MMTK.Collections import Collection
from MMTK.Trajectory import Trajectory
from MMTK.ChemicalObjects import isChemicalObject

from MDANSE import ELEMENTS
from MDANSE.Core.Error import Error
from MDANSE.Extensions import fast_calculation

class MolecularDynamicsError(Error):
    pass

class UniverseAdapterError(Error):
    pass

def atomindex_to_moleculeindex(universe):
    
    d = {}
    for i,obj in enumerate(universe.objectList()):
        if isChemicalObject(obj):
            for at in obj.atomList():
                d[at.index] = i
                
    return d
    
def brute_formula(molecule, sep='_'):
    
    contents = {}
    
    for at in molecule.atomList():
        contents[at.symbol] = str(int(contents.get(at.symbol,0)) + 1)
    
    return sep.join([''.join(v) for v in sorted(contents.items())])

def build_connectivity(universe ,tolerance=0.05):
    
    bonds = []
    
    conf = universe.contiguousObjectConfiguration()

    scannedObjects = [obj for obj in universe.objectList() if isinstance(obj,AtomCluster)]
    singleAtomsObjects = [obj for obj in universe.objectList() if isinstance(obj,Atom) or obj.numberOfAtoms()==1]
    if singleAtomsObjects:
        scannedObjects.append(Collection(singleAtomsObjects))
                
    for obj in scannedObjects:
                                                        
        atoms = sorted(obj.atomList(), key = operator.attrgetter('index'))
        nAtoms = len(atoms)
        indexes = [at.index for at in atoms]
        coords = conf.array[indexes,:]
        covRadii = numpy.zeros((nAtoms,), dtype=numpy.float64)
        for i,at in enumerate(atoms):
            covRadii[i] = ELEMENTS[at.symbol.capitalize(),'covalent_radius']
        
        bonds = []
        fast_calculation.cpt_cluster_connectivity(coords,covRadii,tolerance,bonds)
                  
        for idx1,idx2 in bonds:
            if hasattr(atoms[idx1],"bonded_to__"):
                atoms[idx1].bonded_to__.append(atoms[idx2])
            else:
                atoms[idx1].bonded_to__ = [atoms[idx2]]
                  
            if hasattr(atoms[idx2],"bonded_to__"):
                atoms[idx2].bonded_to__.append(atoms[idx1])
            else:
                atoms[idx2].bonded_to__ = [atoms[idx1]]    

def find_atoms_in_molecule(universe, moleculeName, atomNames, indexes=False):

    molecules = []
    for obj in universe.objectList():
        if isChemicalObject(obj):
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
        if isChemicalObject(obj):
            if d.has_key(obj.name):
                continue
            d[obj.name] = obj.numberOfAtoms()
        
    return d

def get_chemical_objects_dict(universe):
    
    d = {}
    for obj in universe.objectList():
        if isChemicalObject(obj):
            d.setdefault(obj.name, []).append(obj)
        
    return d
        
def get_chemical_objects_number(universe):
    
    d = {}
    for obj in universe.objectList():
        if isChemicalObject(obj):
            if d.has_key(obj.name):
                d[obj.name] += 1
            else:
                d[obj.name] = 1
        
    return d
                                                                    
def partition_universe(universe,groups):
    
    atoms = sorted(universe.atomList(), key = operator.attrgetter('index'))
                                        
    coll = [Collection([atoms[index] for index in gr]) for gr in groups]
    
    return coll

def read_atoms_trajectory(trajectory, atoms, first, last=None, step=1, variable="configuration", weights=None, dtype=numpy.float64):
    
    if not isinstance(atoms,(list,tuple)):
        atoms = [atoms]
        
    if last is None:
        last = len(trajectory)
        
    nFrames = len(range(first, last, step))
    
    serie = numpy.zeros((nFrames,3), dtype=dtype)
    
    if weights is None:
        weights = [1.0]*len(atoms)

    for i,at in enumerate(atoms):
        w = weights[i]
        serie += w*trajectory.readParticleTrajectory(at, first, last, step, variable).array
                
    serie /= sum(weights)
    
    return serie

def resolve_undefined_molecules_name(universe):
    
    for obj in universe.objectList():        
        if isChemicalObject(obj):            
            if not obj.name.strip():
                obj.name = brute_formula(obj,sep="")

def sorted_atoms(universe,attribute=None):

    atoms = sorted(universe.atomList(), key = operator.attrgetter('index'))
    
    if attribute is None:
        return atoms
    else:
        return [getattr(at,attribute) for at in atoms]
    
class MMTKTrajectory(Trajectory):
    
    def __init__(self,*args,**kwargs):
        
        Trajectory.__init__(self,*args,**kwargs)
        
        resolve_undefined_molecules_name(self.universe)
         
        build_connectivity(self.universe)
               

