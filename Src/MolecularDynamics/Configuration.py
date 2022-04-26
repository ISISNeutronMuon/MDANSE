import abc

import numpy as np

from MDANSE.Extensions import atoms_in_shell

class _Configuration:

    __metaclass__ = abc.ABCMeta

    def __init__(self, chemical_system, coordinates, unit_cell=None):

        self._chemical_system = chemical_system

        self._variables = {}

        coordinates = np.array(coordinates)
        if coordinates.shape != (self._chemical_system.number_of_atoms(),3):
            raise ValueError('Invalid coordinates dimensions')

        self['coordinates'] = coordinates

        if unit_cell is not None:

            unit_cell = np.array(unit_cell)

            if unit_cell.shape != (3,3):
                raise ValueError('Invalid unit cell dimensions')

            self._unit_cell = unit_cell

            self._inverse_unit_cell = np.linalg.inv(self._unit_cell)

        else:
            self._unit_cell = None
            self._inverse_unit_cell = None

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
    def inverse_unit_cell(self):
        return self._inverse_unit_cell

    @property
    def is_periodic(self):
        return self._unit_cell is not None

    @property
    def unit_cell(self):
        return self._unit_cell

    @property
    def variables(self):
        return self._variables

class BoxConfiguration(_Configuration):

    def fold_coordinates(self):

        if self._unit_cell is None:
            return

        frac, _ = np.modf(self._variables['coordinates'])
        frac = np.where(frac < 0.0, frac + 1.0, frac)
        frac = np.where(frac > 0.5, frac - 1.0, frac)

        self._variables['coordinates'] = frac

    def to_box_coordinates(self):

        return self._variables['coordinates']

    def to_real_coordinates(self):

        if self._unit_cell is None:
            return
        else:
            return np.matmul(self._variables['coordinates'],self._unit_cell)

    def atomsInShell(self, ref, mini=0.0, maxi=10.0):

        if self._unit_cell is not None:
            indexes = atoms_in_shell.atoms_in_shell_box(self._variables['coordinates'],
                                                        ref,
                                                        mini,
                                                        maxi)
        else:
            indexes = atoms_in_shell.atoms_in_shell_nopbc(self._variables['coordinates'],
                                                          ref,
                                                          mini,
                                                          maxi)
        
        atom_list = self._chemical_system.atom_list()

        selected_atoms = [atom_list[idx] for idx in indexes]

        return selected_atoms

class RealConfiguration(_Configuration):

    def fold_coordinates(self):

        if self._unit_cell is None:
            return

        box_coordinates = self.to_box_coordinates()

        frac, _ = np.modf(box_coordinates)
        frac = np.where(frac < 0.0, frac + 1.0, frac)
        frac = np.where(frac > 0.5, frac - 1.0, frac)

        self._variables['coordinates'] = np.matmul(frac,self._unit_cell)

    def to_box_coordinates(self):

        if self._inverse_unit_cell is None:
            return self._variables['coordinates']
        else:
            return np.matmul(self._variables['coordinates'],self._inverse_unit_cell)

    def to_real_coordinates(self):

        return self._variables['coordinates']

    def atomsInShell(self, ref, mini=0.0, maxi=10.0):

        if self._unit_cell is not None:
            indexes = atoms_in_shell.atoms_in_shell_real(self._variables['coordinates'],
                                                    self._unit_cell,
                                                    self._inverse_unit_cell,
                                                    ref,
                                                    mini,
                                                    maxi)
        else:
            indexes = atoms_in_shell.atoms_in_shell_nopbc(self._variables['coordinates'],
                                                          ref,
                                                          mini,
                                                          maxi)

        atom_list = self._chemical_system.atom_list()

        selected_atoms = [atom_list[idx] for idx in indexes]

        return selected_atoms


if __name__ == "__main__":

    np.random.seed(1)

    from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem

    n_atoms = 2
    cs = ChemicalSystem()
    for i in range(n_atoms):
        cs.add_chemical_entity(Atom(symbol='H'))
        
    coordinates = np.empty((n_atoms,3),dtype=float)
    coordinates[0,:] = [1,1,1]
    coordinates[1,:] = [3,3,3]
    print(coordinates)

    uc = np.array([[10.0,0.0,0.0],[0.0,10.0,0.0],[0.0,0.0,10.0]])

    conf = RealConfiguration(cs, coordinates)

    print(conf.atomsInShell(0,0,5))







