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
from MDANSE.Extensions import atomic_trajectory, com_trajectory, fast_calculation
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
               
class TrajectoryError(Exception):
    pass

class Trajectory:

    def __init__(self, h5_filename):

        self._chemical_system = ChemicalSystem()

        self._h5_filename = h5_filename

        self._h5_file = h5py.File(self._h5_filename,'r')

        self._chemical_system.load(self._h5_filename)

        coords = self._h5_file['/configuration/coordinates'][0,:,:]
        unit_cell = self._h5_file.get('unit_cell',None)
        if unit_cell:
            unit_cell = unit_cell[0,:,:]

        conf = RealConfiguration(self._chemical_system,coords,unit_cell)
        self._chemical_system.configuration = conf

        self.load_unit_cells()

        resolve_undefined_molecules_name(self._chemical_system)
         
        build_connectivity(self._chemical_system, unit_cell=conf.unit_cell)

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

    def configuration(self, frame):

        if frame < 0 or frame >= len(self):
            raise TrajectoryError('Invalid frame number')

        if 'unit_cell' in self._h5_file:
            unit_cell = self._h5_file['unit_cell'][frame,:,:]
        else:
            unit_cell = None

        variables = {}
        for k,v in self._h5_file['configuration'].items():
            variables[k] = v[frame,:,:]

        coordinates = variables.pop('coordinates')

        conf = RealConfiguration(self._chemical_system,coordinates,unit_cell,**variables)

        return conf

    def load_unit_cells(self):

        if 'unit_cell' in self._h5_file:
            
            self._unit_cells = np.empty((len(self),3,3),dtype=np.float)
            self._inverse_unit_cells = np.empty((len(self),3,3),dtype=np.float)

            for i, uc in enumerate(self._h5_file['unit_cell'][:]):
                self._unit_cells[i,:,:] = uc.T
                self._inverse_unit_cells[i,:,:] = np.linalg.inv(self._unit_cells[i,:,:])
        else:
            self._unit_cells = None
            self._inverse_unit_cells = None

    def unit_cell(self,frame):

        if frame < 0 or frame >= len(self):
            raise TrajectoryError('Invalid frame number')

        if 'unit_cell' in self._h5_file:
            return self._h5_file['unit_cell'][frame]        
        else:
            return None

    def __len__(self):

        grp = self._h5_file['/configuration']

        return grp['coordinates'].shape[0]

    def read_atom_trajectory(self, index):

        grp = self._h5_file['/configuration']

        traj = grp['coordinates'][:,index,:]

        return traj

    def read_com_trajectory(self, atoms, first=0, last=None, step=1, box_coordinates=False):

        if last is None:
            last = len(self)

        indexes = [at.index for at in atoms]
        masses = np.array([ATOMS_DATABASE[at.symbol]['atomic_weight'] for at in atoms])

        grp = self._h5_file['/configuration']

        coords = grp['coordinates'][first:last:step,:,:]

        if coords.ndim == 2:
            coords = coords[np.newaxis,:,:]

        if self._unit_cells is not None:
            unit_cells = self._unit_cells[first:last:step]
            inverse_unit_cells = self._inverse_unit_cells[first:last:step]

            top_lvl_chemical_entities = set([at.top_level_chemical_entity() for at in atoms])
            top_lvl_chemical_entities_indexes = [[at.index for at in e.atom_list()] for e in top_lvl_chemical_entities]
            bonds = {}
            for at in self._chemical_system.atom_list():
                bonds[at.index] = [bat.index for bat in at.bonds]

            com_traj = com_trajectory.com_trajectory(
                coords,
                unit_cells,
                inverse_unit_cells,
                masses,
                top_lvl_chemical_entities_indexes,
                indexes,
                bonds,
                box_coordinates=box_coordinates)
        
        else:
            com_traj = np.sum(coords[:,indexes,:]*masses[np.newaxis,:,np.newaxis],axis=1)
            com_traj /= np.sum(masses)

        return com_traj

    def read_atomic_trajectory(self, index, first=0, last=None, step=1, box_coordinates=False):

        if last is None:
            last = len(self)

        grp = self._h5_file['/configuration']
        coords = grp['coordinates'][first:last:step,index,:]

        if self._unit_cells is not None:
            unit_cells = self._unit_cells[first:last:step]
            inverse_unit_cells = self._inverse_unit_cells[first:last:step]
            atomic_traj = atomic_trajectory.atomic_trajectory(coords,unit_cells,inverse_unit_cells,box_coordinates)
            return atomic_traj
        else:
            return coords

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

        self._chemical_system.serialize(self._h5_file)

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
                                                        maxshape=(None,n_atoms,3),chunks=(1,n_atoms,3))
            else:
                dset = configuration_grp[k]
                dset.resize((dset.shape[0]+1,n_atoms,3))
                dset[-1] = v

        unit_cell = configuration.unit_cell
        if unit_cell is not None:
            if 'unit_cell' not in self._h5_file:
                self._h5_file.create_dataset('unit_cell',data=unit_cell[np.newaxis,:,:],maxshape=(None,3,3),chunks=(1,3,3))
            else:
                unit_cell_dset = self._h5_file['unit_cell']
                unit_cell_dset.resize((unit_cell_dset.shape[0]+1,3,3))
                unit_cell_dset[-1] = unit_cell

        if 'time' not in self._h5_file:
            self._h5_file.create_dataset('time',data=[time],maxshape=(None,),dtype=float)
        else:
            dset = self._h5_file['time']
            dset.resize((dset.shape[0]+1,))
            dset[-1] = time

class RigidBodyTrajectory:
    """
    Rigid-body trajectory data

    If rbt is a RigidBodyTrajectory object, then

     * len(rbt) is the number of steps stored in it
     * rbt[i] is the value at step i (a vector for the center of mass
       and a quaternion for the orientation)
    """
    
    def __init__(self, trajectory, chemical_entity, first=0, last=None, step=1, reference=0):

        self._trajectory = trajectory
        
        if last is None:
            last = len(self._trajectory)

        reference = self._trajectory.configuration(reference)
        continuous_configuration = reference.continuous_configuration()
        self._trajectory.chemical_system.configuration = continuous_configuration
        mass = chemical_entity.mass()
        ref_cms = chemical_entity.center_of_mass()
        print(ref_cms)
        atoms = chemical_entity.atom_list()

        n_steps = len(range(first,last,step))

        possq = np.zeros((n_steps,), np.float)
        cross = np.zeros((n_steps, 3, 3), np.float)

        masses = np.array([ATOMS_DATABASE[at.symbol]['atomic_weight'] for at in atoms])

        rcms = self._trajectory.read_com_trajectory(chemical_entity.atom_list(),first,last,step,box_coordinates=True)

        # relative coords of the CONTIGUOUS reference
        r_ref = np.zeros((len(atoms), 3), np.float)
        for a in range(len(atoms)):
            if a == 0:
                print(atoms[a])
                print('ref',continuous_configuration['coordinates'][a,:], ref_cms)
            r_ref[a] = continuous_configuration['coordinates'][a,:] - ref_cms
        print(r_ref[0,:])

        # main loop: storing data needed to fill M matrix 
        for a in range(len(atoms)):
            r = self._trajectory.read_atomic_trajectory(a,first, last, step, True)

            r = r - rcms
            # if offset is not None:
            #     numpy.add(r, offset[atoms[a]].array,r)
            # trajectory._boxTransformation(r, r)
            w = masses[a]/mass
            np.add(possq, w*np.add.reduce(r*r, -1), possq)
            np.add(possq, w*np.add.reduce(r_ref[a]*r_ref[a],-1),possq)
            np.add(cross, w*r[:,:,np.newaxis]*r_ref[np.newaxis,a,:],cross)
        # self.trajectory._boxTransformation(rcms, rcms)

        # filling matrix M (formula no 40)
        k = np.zeros((n_steps, 4, 4), np.float)
        k[:, 0, 0] = -cross[:, 0, 0]-cross[:, 1, 1]-cross[:, 2, 2]
        k[:, 0, 1] = cross[:, 1, 2]-cross[:, 2, 1]
        k[:, 0, 2] = cross[:, 2, 0]-cross[:, 0, 2]
        k[:, 0, 3] = cross[:, 0, 1]-cross[:, 1, 0]
        k[:, 1, 1] = -cross[:, 0, 0]+cross[:, 1, 1]+cross[:, 2, 2]
        k[:, 1, 2] = -cross[:, 0, 1]-cross[:, 1, 0]
        k[:, 1, 3] = -cross[:, 0, 2]-cross[:, 2, 0]
        k[:, 2, 2] = cross[:, 0, 0]-cross[:, 1, 1]+cross[:, 2, 2]
        k[:, 2, 3] = -cross[:, 1, 2]-cross[:, 2, 1]
        k[:, 3, 3] = cross[:, 0, 0]+cross[:, 1, 1]-cross[:, 2, 2]
        del cross
        for i in range(1, 4):
            for j in range(i):
                k[:, i, j] = k[:, j, i]
        np.multiply(k, 2., k)
        for i in range(4):
            np.add(k[:,i,i], possq, k[:,i,i])
        del possq

        quaternions = np.zeros((n_steps, 4), np.float)
        fit = np.zeros((n_steps,), np.float)
        for i in range(n_steps):
            e, v = np.linalg.eig(k[i])
            v = np.transpose(v)
            j = np.argmin(e)
            if e[j] < 0.0:
                fit[i] = 0.
            else:
                fit[i] = np.sqrt(e[j])
            if v[j,0] < 0.0:
                quaternions[i] = -v[j]
            else:
                quaternions[i] = v[j]
        self.fit = fit
        self.cms = rcms
        self.quaternions = quaternions

    def __len__(self):
        return self.cms.shape[0]

    def __getitem__(self, index):
        from MDANSE.Mathematics.Geometry import Vector
        from MDANSE.Mathematics.LinearAlgebra import Quaternion
        return Vector(self.cms[index]), Quaternion(self.quaternions[index])

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


