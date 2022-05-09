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

import h5py

from MMTK.Collections import Collection
from MMTK.Trajectory import Trajectory

from MDANSE.Core.Error import Error
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Extensions import com_trajectory, fast_calculation
from MDANSE.MolecularDynamics.Configuration import RealConfiguration

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

def build_connectivity(chemicalSystem ,tolerance=0.05):
    
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
        
        fast_calculation.cpt_cluster_connectivity(coords,covRadii,tolerance,bonds)
                  
        for idx1,idx2 in bonds:
            if hasattr(atoms[idx1],"bonded_to__"):
                atoms[idx1].bonds.append(atoms[idx2])
            else:
                atoms[idx1].bonds = [atoms[idx2]]
                  
            if hasattr(atoms[idx2],"bonded_to__"):
                atoms[idx2].bonds.append(atoms[idx1])
            else:
                atoms[idx2].bonds = [atoms[idx1]]    

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
               
class TrajectoryError(Exception):
    pass

class Trajectory:

    def __init__(self, h5_filename):

        self._chemical_system = ChemicalSystem()

        self._h5_filename = h5_filename

        self._h5_file = h5py.File(self._h5_filename,'r')

        self._chemical_system.load(self._h5_filename)

        coords = self._h5_file['/configuration/coordinates'][0,:,:]
        unit_cell = self._h5_file['/configuration'].get('unit_cell',None)
        if unit_cell:
            unit_cell = unit_cell[0,:,:]

        conf = RealConfiguration(self._chemical_system,coords,unit_cell)
        self._chemical_system.configuration = conf
        
        resolve_undefined_molecules_name(self._chemical_system)
         
        build_connectivity(self._chemical_system)

    def close(self):

        self._h5_file.close()

    def __getitem__(self,item):

        grp = self._h5_file['/configuration']

        configuration = {}
        for k, v in grp.items():
            configuration[k] = v[item]

        return configuration

    def coordinates(self,frame):

        if frame < 0 or frame >= len(self):
            raise TrajectoryError('Invalid frame number')

        grp = self._h5_file['/configuration']

        return grp['coordinates'][frame]        

    def unit_cell(self,frame):

        if frame < 0 or frame >= len(self):
            raise TrajectoryError('Invalid frame number')

        grp = self._h5_file['/configuration']

        if 'unit_cell' in grp:
            return grp['unit_cell'][frame]        
        else:
            return None

    def __len__(self):

        grp = self._h5_file['/configuration']

        return grp['coordinates'].shape[0]

    def read_atom_trajectory(self, index):

        grp = self._h5_file['/configuration']

        traj = grp['coordinates'][:,index,:]

        return traj

    def _read_com_trajectory_nopbc(self, coords, indexes, masses):

        cog_traj = np.sum(coords*masses[np.newaxis,:,np.newaxis],axis=1)
        cog_traj /= np.sum(masses)

        return cog_traj

    def read_com_trajectory(self, indexes, masses, first, last, step=1):

        grp = self._h5_file['/configuration']

        coords = grp['coordinates'][first:last:step,indexes,:]

        if 'unit_cell' in grp:
            n_frames = coords.shape[0]
            unit_cells = np.empty(n_frames,3,3)
            inverse_unit_cells = np.empty(n_frames,3,3)
            for i, uc in enumerate(grp['unit_cell'][first:last:step]):
                unit_cells[i,:,:] = uc.T
                inverse_unit_cells = np.linalg.inv(unit_cells[i,:,:])
            cog_traj = com_trajectory.com_trajectory(coords,
                                                     unit_cells,
                                                     inverse_unit_cells,
                                                     masses)
        
        else:
            cog_traj = self._com_trajectory_nopbc(coords, indexes, masses)

        return cog_traj

    @property
    def chemical_system(self):
        return self._chemical_system

    @property
    def h5_file(self):
        return self._h5_file

    @property
    def h5_filename(self):
        return self._h5_filename

class TrajectoryWriterError(Exception):
    pass

class TrajectoryWriter:

    def __init__(self, h5_filename, chemical_system, selected_atoms=None):

        self._h5_filename = h5_filename

        self._h5_file = h5py.File(self._h5_filename,'w')

        self._chemical_system = chemical_system

        if selected_atoms is None:
            self._selected_atoms = self._chemical_system.atom_list()
        else:
            for at in selected_atoms:
                if at.root_chemical_system() != self._chemical_system:
                    raise TrajectoryWriterError('One or more atoms of the selection comes from a different chemical system')
            self._selected_atoms = sorted_atoms(selected_atoms)
        self._selected_atoms = [at.index for at in self._selected_atoms]

        self._dump_chemical_system()

        self._h5_file.create_group('/configuration')

    def _dump_chemical_system(self):

        string_dt = h5py.special_dtype(vlen=str)

        grp = self._h5_file.create_group('/chemical_system')

        h5_contents = {}

        contents = []
        for ce in self._chemical_system.chemical_entities:
            entity_type, entity_index = ce.serialize(self._h5_file, h5_contents)
            contents.append((entity_type,str(entity_index)))

        for k,v in h5_contents.items():
            grp.create_dataset(k,data=v,dtype=string_dt)
        grp.create_dataset('contents', data=contents, dtype=string_dt)

    def close(self):
        self._h5_file.close()

    def dump_configuration(self, time):

        configuration = self._chemical_system.configuration
        if configuration is None:
            return

        n_atoms = self._chemical_system.number_of_atoms()

        configuration_grp = self._h5_file['/configuration']
        for k, v in configuration.variables.items():
            if not k in configuration_grp:
                dset = configuration_grp.create_dataset(k,
                                                        data=v[np.newaxis,:,:],
                                                        maxshape=(None,n_atoms,3))
            else:
                dset = configuration_grp[k]
                dset.resize((dset.shape[0]+1,n_atoms,3))
                dset[-1] = v

        unit_cell = configuration.unit_cell
        inverse_unit_cell = configuration.inverse_unit_cell
        if unit_cell is not None:
            if 'unit_cell' not in configuration_grp:
                configuration_grp.create_dataset('unit_cell',data=unit_cell[np.newaxis,:,:],maxshape=(None,3,3))
                configuration_grp.create_dataset('inverse_unit_cell',data=inverse_unit_cell[np.newaxis,:,:],maxshape=(None,3,3))
            else:
                unit_cell_dset = configuration_grp['unit_cell']
                unit_cell_dset.resize((unit_cell_dset.shape[0]+1,3,3))
                unit_cell_dset[-1] = unit_cell

                inverse_unit_cell_dset = configuration_grp['inverse_unit_cell']
                inverse_unit_cell_dset.resize((inverse_unit_cell_dset.shape[0]+1,3,3))
                inverse_unit_cell_dset[-1] = inverse_unit_cell


        if 'time' not in configuration_grp:
            configuration_grp.create_dataset('time',data=[time],maxshape=(None,),dtype=float)
        else:
            dset = configuration_grp['time']
            dset.resize((dset.shape[0]+1,))
            dset[-1] = time

if __name__ == '__main__':

    # t = Trajectory('test.h5')
    # cs = t.chemical_system
    # t.close()
    
    # from Configuration import RealConfiguration
    # import numpy as np

    # coordinates = np.random.uniform(0,10,(30714,3))
    # unit_cell = np.random.uniform(0,10,(3,3))
    # conf = RealConfiguration(cs,coordinates,unit_cell)

    # cs.configuration = conf

    # tw = TrajectoryWriter('toto.h5',cs)
    # tw.dump_configuration()
    # tw.close()

    # t = Trajectory('toto.h5')
    # print(t.read_atom_trajectory(2))
    # t.close()

    # import numpy as np

    # from MDANSE.MolecularDynamics.Configuration import RealConfiguration

    # from MDANSE.Chemistry.ChemicalEntity import Atom
    # cs = ChemicalSystem()
    # for i in range(768):
    #     cs.add_chemical_entity(Atom(symbol='H'))

    # coords = np.load('coords.npy')
    # unit_cell = np.load('unit_cell.npy')
    
    # tw = TrajectoryWriter('waterbox.h5',cs)

    # n_frames = coords.shape[0]
    # for i in range(n_frames):
    #     c = RealConfiguration(cs,coords[i,:,:],unit_cell[i,:,:])
    #     cs.configuration = c
    #     tw.dump_configuration()
    
    # tw.close()

    # t = Trajectory('waterbox.h5')
    # t.close()

    from MDANSE.MolecularDynamics.Configuration import RealConfiguration

    from MDANSE.Chemistry.ChemicalEntity import Atom
    cs = ChemicalSystem()
    for i in range(2):
        cs.add_chemical_entity(Atom(symbol='H'))

    tw = TrajectoryWriter('test.h5',cs)
    unit_cell = 10.0*np.identity(3)

    coords = np.empty((2,3),dtype=np.float)
    coords[0,:] = [-4,0,0]
    coords[1,:] = [ 4,0,0]

    c = RealConfiguration(cs,coords,unit_cell)
    cs.configuration = c
    tw.dump_configuration(1.0)
    tw.close()

    t = Trajectory('test.h5')
    print(t.read_cog_trajectory([0,1],0,10,1).shape)
    t.close()


