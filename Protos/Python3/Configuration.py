import abc

import numpy as np

class _Configuration:

    __metaclass__ = abc.ABCMeta

    def __init__(self, chemical_system, coordinates, unit_cell=None):

        self._chemical_system = chemical_system

        self._variables = {}

        coordinates = np.array(coordinates)

        self['coordinates'] = coordinates

        if unit_cell is not None:

            unit_cell = np.array(unit_cell)

            if unit_cell.shape != (3,3):
                raise ValueError('Invalid unit cell dimensions')

        self._unit_cell = unit_cell

        self._inverse_unit_cell = np.linalg.inv(self._unit_cell)

    def __getitem__(self, name):

        return self._variables[name]

    def __setitem__(self, name, item):

        item = np.array(item)
        if item.shape != (self._chemical_system.number_of_atoms(),3):
            raise ValueError('Invalid item dimensions')

        self._variables[name] = item

    @property
    def chemical_system(self):
        return self._chemical_system

    @property
    def coordinates(self):
        return self._coordinates

    @abc.abstractmethod
    def fold_coordinates(self):
        pass

    @abc.abstractmethod
    def to_box_coordinates(self):
        pass

    @abc.abstractmethod
    def to_real_coordinates(self):
        pass

    @property
    def coordinates(self):
        return self._variables['coordinates']

    @property
    def unit_cell(self):
        return self._unit_cell

    @property
    def variables(self):
        return self._variables

class BoxConfiguration(_Configuration):

    def __init__(self, chemical_system, coordinates, unit_cell):

        super(BoxConfiguration,self).__init__(chemical_system,coordinates,unit_cell)

    def fold_coordinates(self):
        pass

    def to_box_coordinates(self):

        return self._variables['coordinates']

    def to_real_coordinates(self):

        return np.matmul(self._unit_cell,self._variables['coordinates'].T).T

class RealConfiguration(_Configuration):

    def fold_coordinates(self):

        box_coordinates = self.to_box_coordinates()

        frac, _ = np.modf(box_coordinates)
        frac = np.where(frac < 0.0, frac + 1.0, frac)
        frac = np.where(frac > 0.5, frac - 1.0, frac)

        self._variables['coordinates'] = np.matmul(self._unit_cell,frac.T).T

    def to_box_coordinates(self):
        
        # print(np.matmul(self._unit_cell,self._variables['coordinates'][0,:].T).T)
        return np.matmul(self._inverse_unit_cell,self._variables['coordinates'].T).T

    def to_real_coordinates(self):

        return self._variables['coordinates']

if __name__ == "__main__":

    np.random.seed(1)

    from ChemicalEntity import Atom, ChemicalSystem

    n_atoms = 5
    cs = ChemicalSystem()
    for i in range(n_atoms):
        cs.add_chemical_entity(Atom(symbol='H'))
        
    coordinates = np.random.uniform(-10,10,(n_atoms,3))
    print(coordinates)

    uc = np.array([[1.0,2.0,3.0],[2.0,-1.0,3.0],[1.0,1.0,1.0]]).T
    # uc = np.array([[10.0,0.0,0.0],[0.0,10.0,0.0],[0.0,0.0,10.0]]).T

    conf = RealConfiguration(cs, coordinates, uc)

    conf.fold_coordinates()

    # print(conf.to_box_coordinates())

    # conf = BoxConfiguration(cs, coordinates, uc)

    # print(conf.to_real_coordinates())






