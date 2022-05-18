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

from MMTK.Trajectory import Trajectory

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.Extensions import atomic_trajectory, com_trajectory, fold_coordinates
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.MolecularDynamics.TrajectoryUtils import build_connectivity, resolve_undefined_molecules_name, sorted_atoms

class TrajectoryError(Exception):
    pass

class Trajectory:

    def __init__(self, h5_filename):
        """Constructor.

        :param h5_filename: the trajectory filename
        :type h5_filename: str
        """

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

        self._load_unit_cells()

        resolve_undefined_molecules_name(self._chemical_system)

        build_connectivity(self._chemical_system, unit_cell=conf.unit_cell)

    def close(self):
        """Close the trajectory.
        """

        self._h5_file.close()

    def __getitem__(self,frame):
        """Return the configuration at a given frame

        :param frame: the frame
        :type frame: int

        :return: the configuration
        :rtype: dict of ndarray
        """

        grp = self._h5_file['/configuration']

        configuration = {}
        for k, v in grp.items():
            configuration[k] = v[frame]

        return configuration

    def coordinates(self,frame):
        """Return the coordinates at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the coordinates
        :rtype: ndarray
        """

        if frame < 0 or frame >= len(self):
            raise TrajectoryError('Invalid frame number')

        grp = self._h5_file['/configuration']

        return grp['coordinates'][frame]

    def configuration(self, frame):
        """Build and return a configuration at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the configuration
        :rtype: MDANSE.MolecularDynamics.Configuration.Configuration
        """

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

    def _load_unit_cells(self):
        """Load all the unit cells and their corresponding inverse.
        """

        if 'unit_cell' in self._h5_file:
            
            self._unit_cells = np.empty((len(self),3,3),dtype=np.float)
            self._inverse_unit_cells = np.empty((len(self),3,3),dtype=np.float)

            for i, uc in enumerate(self._h5_file['unit_cell'][:]):
                self._unit_cells[i,:,:] = uc.T
                self._inverse_unit_cells[i,:,:] = np.linalg.inv(self._unit_cells[i,:,:])
        else:
            self._unit_cells = None
            self._inverse_unit_cells = None

    def get_unit_cells(self):
        """Return the direct and inverse unit cells.

        :return: the directand inverse unit cells
        :rtype: tuple
        """

        if self._unit_cells is None:
            return (None,None)

        else:
            return (self._unit_cells, self._inverse_unit_cells)

    def unit_cell(self,frame):
        """Return the unit cell at a given frame. If no unit cell is defined, returns None.

        :return: the unit cell
        :rtype: ndarray
        """

        if frame < 0 or frame >= len(self):
            raise TrajectoryError('Invalid frame number')

        if 'unit_cell' in self._h5_file:
            return self._h5_file['unit_cell'][frame]        
        else:
            return None

    def __len__(self):
        """Returns the length of the trajectory.

        :return: the number of frames of the trajectory
        :rtype: int
        """

        grp = self._h5_file['/configuration']

        return grp['coordinates'].shape[0]

    def read_com_trajectory(self, atoms, first=0, last=None, step=1, box_coordinates=False):
        """Build the trajectory of the center of mass of a set of atoms.

        :param atoms: the atoms for which the center of mass should be computed
        :type atoms: list MDANSE.Chemistry.ChemicalEntity.Atom
        :param first: the index of the first frame
        :type first: int
        :param last: the index of the last frame
        :type last: int
        :param step: the step in frame
        :type step: int
        :param box_coordinates: if True, the coordiniates are returned in box coordinates
        :type step: bool

        :return: 2D array containing the center of mass trajectory for the selected frames
        :rtype: ndarray
        """

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
            for e in top_lvl_chemical_entities:
                for at in e.atom_list():
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

    def to_real_coordinates(self, box_coordinates, first, last, step):
        """Convert box coordinates to real coordinates for a set of frames.

        :param box_coordinates: a 2D array containing the box coordinates
        :type box_coordinates: ndarray
        :param first: the index of the first frame
        :type first: int
        :param last: the index of the last frame
        :type last: int
        :param step: the step in frame
        :type step: int

        :return: 2D array containing the real coordinates converted from box coordinates.
        :rtype: ndarray
        """

        if self._unit_cells is not None:
            real_coordinates = np.empty(box_coordinates.shape,dtype=np.float)
            comp = 0
            for i in range(first,last,step):
                unit_cell = self._unit_cells[i]
                real_coordinates[comp,:] = np.matmul(unit_cell,box_coordinates[comp,:])
                comp += 1
            return real_coordinates
        else:
            return box_coordinates

    def read_atomic_trajectory(self, index, first=0, last=None, step=1, box_coordinates=False):
        """Read an atomic trajectory. The trajectory is corrected from box jumps.

        :param index: the index of the atom
        :type index: int
        :param first: the index of the first frame
        :type first: int
        :param last: the index of the last frame
        :type last: int
        :param step: the step in frame
        :type step: int
        :param box_coordinates: if True, the coordiniates are returned in box coordinates
        :type step: bool

        :return: 2D array containing the atomic trajectory for the selected frames
        :rtype: ndarray
        """

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
        """Return the chemical system stored in the trajectory.

        :return: the chemical system
        :rtype: MDANSE.Chemistry.ChemicalEntity.ChemicalSystem
        """
        return self._chemical_system

    @property
    def h5_file(self):
        """Return the trajectory file object.

        :return: the trajectory file object
        :rtype: HDF5 file object
        """

        return self._h5_file

    @property
    def h5_filename(self):
        """Return the trajectory filename.

        :return: the trajectory filename
        :rtype: str
        """

        return self._h5_filename

class TrajectoryWriterError(Exception):
    pass

class TrajectoryWriter:

    def __init__(self, h5_filename, chemical_system, n_steps, selected_atoms=None):
        """Constructor.

        :param h5_filename: the trajectory filename
        :type h5_filename: str
        :param chemical_system: the chemical system
        :type h5_filename: MDANSE.Chemistry.ChemicalEntity.ChemicalSystem
        :param h5_filename: the number of steps
        :type h5_filename: int
        :param selected_atoms: the selected atoms of the chemical system to write
        :type selected_atoms: list of MDANSE.Chemistry.ChemicalEntity.Atom
        """

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

        self._n_steps = n_steps

        self._current_index = 0

    def _dump_chemical_system(self):
        """Dump the chemical system to the trajectory file.
        """

        self._chemical_system.serialize(self._h5_file)

    def close(self):
        """Close the trajectory file
        """

        self._h5_file.close()

    def dump_configuration(self, time):
        """Dump the chemical system configuration at a given time.

        :param time: the time
        :type time: float
        """

        if self._current_index >= self._n_steps:
            raise TrajectoryError('The current steps is greater than the actual number of steps of the trajectory')

        configuration = self._chemical_system.configuration
        if configuration is None:
            return

        n_atoms = self._chemical_system.number_of_atoms()

        configuration_grp = self._h5_file['/configuration']
        for k, v in configuration.variables.items():
            dset = configuration_grp.get(k,None)
            if dset is None:
                dset = configuration_grp.create_dataset(
                    k,
                    shape=(self._n_steps,n_atoms,3),
                    chunks=(1,n_atoms,3),                    
                    dtype=np.float)
            dset[self._current_index] = v

        unit_cell = configuration.unit_cell
        if unit_cell is not None:
            unit_cell_dset = self._h5_file.get('unit_cell',None)
            if unit_cell_dset is None:
                unit_cell_dset = self._h5_file.create_dataset(
                    'unit_cell',
                    shape=(self._n_steps,3,3),
                    chunks=(1,3,3),
                    dtype=np.float)
            unit_cell_dset[self._current_index] = unit_cell

        time_dset = self._h5_file.get('time',None)
        if time_dset is None:
            time_dset = self._h5_file.create_dataset(
                'time',
                shape=(self._n_steps,),
                dtype=np.float)
        time_dset[self._current_index] = time

        self._current_index += 1

class RigidBodyTrajectoryGenerator:
    """Compute the Rigid-body trajectory data

    If rbt is a RigidBodyTrajectory object, then

     * len(rbt) is the number of steps stored in it
     * rbt[i] is the value at step i (a vector for the center of mass
       and a quaternion for the orientation)
    """
    
    def __init__(self, trajectory, chemical_entity, reference, first=0, last=None, step=1):
        """Constructor.

        :param trajectory: the input trajectory
        :type trajectory: MDANSE.Trajectory.Trajectory
        :param chemical_entity: the chemical enitty for which the Rigig-Body trajectory should be computed
        :type chemical_entity: MDANSE.Chemistry.ChemicalEntity.ChemicalEntity
        :param reference: the reference configuration. Must be continuous.
        :type reference: MDANSE.MolecularDynamics.Configuration.Configuration
        :param first: the index of the first frame
        :type first: int
        :param last: the index of the last frame
        :type last: int
        :param step: the step in frame
        :type step: int
        """

        self._trajectory = trajectory
        
        if last is None:
            last = len(self._trajectory)

        atoms = chemical_entity.atom_list()

        masses = [ATOMS_DATABASE[at.symbol]['atomic_weight'] for at in atoms]

        mass = sum(masses)

        ref_com = chemical_entity.center_of_mass(reference)

        n_steps = len(range(first,last,step))

        possq = np.zeros((n_steps,), np.float)
        cross = np.zeros((n_steps, 3, 3), np.float)

        rcms = self._trajectory.read_com_trajectory(atoms,first,last,step,box_coordinates=True)

        # relative coords of the CONTIGUOUS reference
        r_ref = np.zeros((len(atoms), 3), np.float)
        for i, at in enumerate(atoms):
            r_ref[i] = reference['coordinates'][at.index,:] - ref_com

        unit_cells, inverse_unit_cells = self._trajectory.get_unit_cells()
        if unit_cells is not None:
            unit_cells = unit_cells[first:last:step,:,:]
            inverse_unit_cells = inverse_unit_cells[first:last:step,:,:]

        for i, at in enumerate(atoms):
            r = self._trajectory.read_atomic_trajectory(at.index,first, last, step, True)
            r = r - rcms

            r = r[:,np.newaxis,:]
            r = fold_coordinates.fold_coordinates(
                r,
                unit_cells,
                inverse_unit_cells,
                True
            )
            r = np.squeeze(r)            

            r = self._trajectory.to_real_coordinates(r,first,last,step)
            w = masses[i]/mass
            np.add(possq, w*np.add.reduce(r*r, -1), possq)
            np.add(possq, w*np.add.reduce(r_ref[i]*r_ref[i],-1),possq)
            np.add(cross, w*r[:,:,np.newaxis]*r_ref[np.newaxis,i,:],cross)
            
        rcms = self._trajectory.to_real_coordinates(rcms, first, last, step)

        # filling matrix M
        k = np.zeros((n_steps, 4, 4), np.float)
        k[:, 0, 0] = -cross[:, 0, 0]-cross[:, 1, 1]-cross[:, 2, 2]
        k[:, 0, 1] =  cross[:, 1, 2]-cross[:, 2, 1]
        k[:, 0, 2] =  cross[:, 2, 0]-cross[:, 0, 2]
        k[:, 0, 3] =  cross[:, 0, 1]-cross[:, 1, 0]
        k[:, 1, 1] = -cross[:, 0, 0]+cross[:, 1, 1]+cross[:, 2, 2]
        k[:, 1, 2] = -cross[:, 0, 1]-cross[:, 1, 0]
        k[:, 1, 3] = -cross[:, 0, 2]-cross[:, 2, 0]
        k[:, 2, 2] =  cross[:, 0, 0]-cross[:, 1, 1]+cross[:, 2, 2]
        k[:, 2, 3] = -cross[:, 1, 2]-cross[:, 2, 1]
        k[:, 3, 3] =  cross[:, 0, 0]+cross[:, 1, 1]-cross[:, 2, 2]

        for i in range(1, 4):
            for j in range(i):
                k[:, i, j] = k[:, j, i]
        np.multiply(k, 2., k)
        for i in range(4):
            np.add(k[:,i,i], possq, k[:,i,i])

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


