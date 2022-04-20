from numbers import Real
import h5py

from ChemicalEntity import ChemicalSystem

class Trajectory:

    def __init__(self, h5_filename):

        self._chemical_system = ChemicalSystem()

        self._h5_filename = h5_filename

        self._h5_file = h5py.File(self._h5_filename,'r')

        self._chemical_system.load(self._h5_filename)

    def close(self):

        self._h5_file.close()

    def __getitem__(self,item):

        grp = self._h5_file['/configuration']

        configuration = {}
        for k, v in grp.items():
            configuration[k] = v[item,:,:]

        return configuration

    def __len__(self):

        grp = self._h5_file['/configuration']

        return grp['coordinates'].shape[0]

    def read_atom_trajectory(self, index):

        grp = self._h5_file['/configuration']

        n_frames = grp['coordinates'].shape[0]

        traj = grp['coordinates'][:,index,:]

        return traj

    @property
    def chemical_system(self):
        return self._chemical_system

    @property
    def h5_filename(self):
        return self._h5_filename

class TrajectoryWriter:

    def __init__(self, h5_filename, chemical_system):

        self._h5_filename = h5_filename

        self._h5_file = h5py.File(self._h5_filename,'w')

        self._chemical_system = chemical_system

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

    def dump_configuration(self):

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
        if unit_cell is None:
            return

        if 'unit_cell' not in configuration_grp:
            dset = configuration_grp.create_dataset('unit_cell',
                                                    data=unit_cell[np.newaxis,:,:],
                                                    maxshape=(None,3,3))
        else:
            dset = configuration_grp['unit_cell']
            dset.resize((dset.shape[0]+1,n_atoms,3))
            dset[-1] = unit_cell

if __name__ == '__main__':

    t = Trajectory('test.h5')
    cs = t.chemical_system
    t.close()
    
    from Configuration import RealConfiguration
    import numpy as np

    coordinates = np.random.uniform(0,10,(30714,3))
    unit_cell = np.random.uniform(0,10,(3,3))
    conf = RealConfiguration(cs,coordinates,unit_cell)

    cs.configuration = conf

    tw = TrajectoryWriter('toto.h5',cs)
    tw.dump_configuration()
    tw.close()

    t = Trajectory('toto.h5')
    print(t.read_atom_trajectory(2))
    t.close()

