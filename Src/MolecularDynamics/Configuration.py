import abc
import copy

import numpy as np

from MDANSE.Extensions import atoms_in_shell, contiguous_coordinates

class ConfigurationError(Exception):
    pass

class _Configuration(metaclass=abc.ABCMeta):

    def __init__(self, chemical_system,coordinates,**variables):
        """Constructor.

        Args:
            chemical_system (MDANSE.Chemistry.ChemicalEntity.ChemicalSystem): the chemical system
            coordinates (ndarray): the coordinates
        """

        self._chemical_system = chemical_system

        self._variables = {}

        coordinates = np.array(coordinates)
        if coordinates.shape != (self._chemical_system.number_of_atoms(),3):
            raise ValueError('Invalid coordinates dimensions')

        self['coordinates'] = coordinates

        for k,v in variables.items():
            self[k] = v

    def __contains__(self,item):
        """Return True if |item| belong to the configuration.

        Args:
            item (str): the item

        Returns:
            bool: True if the configuration has the given item
        """
        return item in self._variables

    def __getitem__(self,item):
        """Returns the configuration value for a given item.

        Args:
            item (str): the item
        """
        return self._variables[item]

    def __setitem__(self,name,value):
        """Set a configuration item.

        Args:
            name (str): the item
            value (ndarray): the value
        """

        item = np.array(value)
        if item.shape != (self._chemical_system.number_of_atoms(),3):
            raise ValueError('Invalid item dimensions')

        self._variables[name] = value

    def apply_transformation(self,transfo):
        """Apply a linear transformation to the configuration.

        Args:
            transfo (MDANSE.Mathematics.Transformation.Transformation): the transformation
        """
        conf = self['coordinates']
        rot = transfo.rotation().tensor.array
        conf[:] = np.dot(conf, np.transpose(rot))
        np.add(conf, transfo.translation().vector.array[np.newaxis, :], conf)

        if 'velocities' in self._variables:
            velocities = self._variables['velocities']
            rot = transfo.rotation().tensor.array
            velocities[:] = np.dot(velocities, np.transpose(rot))

    @property
    def chemical_system(self):
        """Returns the chemical system stored in this configuration.

        Args:
            chemical_system (MDANSE.Chemistry.ChemicalEntity.ChemicalSystem): the chemical system
        """
        return self._chemical_system

    @abc.abstractmethod
    def clone(self,chemical_system):
        """Clone this configuration.

        Args:
            chemical_system (MDANSE.Chemistry.ChemicalEntity.ChemicalSystem): the chemical system
        """
        pass

    @property
    def coordinates(self):
        """Returns the coordinates.

        Returns:
            ndarray: the coordinates
        """
        return self._variables['coordinates']

    @abc.abstractmethod
    def to_real_coordinates(self):
        """Return the coordinates of this configuration converted to real coordinates.

        Returns:
            ndarray: the real coordinates
        """
        pass

    @property
    def variables(self):
        """Returns the configuration variable dictionary.

        Returns:
            dict: the confguration variables
        """
        return self._variables

class _PeriodicConfiguration(_Configuration):

    def __init__(self, chemical_system, coordinates, unit_cell, **variables):
        """Constructor.

        Args:
            chemical_system (MDANSE.Chemistry.ChemicalEntity.ChemicalSystem): the chemical system
            coordinates (ndarray): the coordinates
            unit_cell (MDANSE.MolecularDynamics.UnitCell.UnitCell): the unit cell
        """

        super(_PeriodicConfiguration,self).__init__(chemical_system,coordinates,**variables)

        if unit_cell.direct.shape != (3,3):
            raise ValueError('Invalid unit cell dimensions')
        self._unit_cell = unit_cell

    def clone(self,chemical_system):
        """Clone this configuration.

        Args:
            chemical_system (MDANSE.Chemistry.ChemicalEntity.ChemicalSystem): the chemical system
        """

        if chemical_system.total_number_of_atoms() != self.chemical_system.total_number_of_atoms():
            raise ConfigurationError('Mismatch between the chemical systems')

        unit_cell = copy.deepcopy(self._unit_cell)

        variables = copy.deepcopy(self.variables)

        coords = variables.pop('coordinates')

        return self.__class__(chemical_system,coords,unit_cell,**variables)
        
    @abc.abstractmethod
    def fold_coordinates(self):
        """Fold the coordinates into simulation box.
        """
        pass

    @abc.abstractmethod
    def to_box_coordinates(self):
        """Return this configuration converted to box coordinates.

        Returns:
            ndarray: the box coordinates
        """
        pass

    @property
    def unit_cell(self):
        """Return the nit cell stored in this configuration.

        Returns:
            MDANSE.MolecularDynamics.UnitCell.UnitCell: the unit cell
        """
        return self._unit_cell

    @unit_cell.setter
    def unit_cell(self,unit_cell):
        """Ses the unit cell.

        Args:
            unit_cell (MDANSE.MolecularDynamics.UnitCell.UnitCell): the unit cell
        """
        self._unit_cell = unit_cell

class PeriodicBoxConfiguration(_PeriodicConfiguration):

    is_periodic = True

    def fold_coordinates(self):
        """Fold the coordinates into simulation box.
        """

        from MDANSE.Extensions import fold_coordinates

        coords = self._variables['coordinates']
        coords = coords[np.newaxis,:,:]
        unit_cell = self._unit_cell.transposed_direct
        inverse_unit_cell = self._unit_cell.transposed_inverse
        unit_cells = unit_cell[np.newaxis,:,:]
        inverse_unit_cells = inverse_unit_cell[np.newaxis,:,:]
        coords = fold_coordinates.fold_coordinates(
            coords,
            unit_cells,
            inverse_unit_cells,
            True
        )
        coords = np.squeeze(coords)
        self._variables['coordinates'] = coords

    def to_box_coordinates(self):
        """Return this configuration converted to box coordinates.

        Returns:
            ndarray: the box coordinates
        """
        return self._variables['coordinates']

    def to_real_coordinates(self):
        """Return the coordinates of this configuration converted to real coordinates.

        Returns:
            ndarray: the real coordinates
        """
        return np.matmul(self._variables['coordinates'],self._unit_cell.direct)

    def to_real_configuration(self):
        """Return this configuration converted to real coordinates.

        Returns:
            MDANSE.MolecularDynamics.Configuration.PeriodicRealConfiguration: the configuration
        """

        coords = self.to_real_coordinates()

        variables = copy.deepcopy(self._variables)
        variables.pop('coordinates')

        real_conf = PeriodicRealConfiguration(self._chemical_system,coords,self._unit_cell,**variables)

        return real_conf

    def atomsInShell(self, ref, mini=0.0, maxi=10.0):
        """Returns the atoms found in a shell around a reference atom.

        Args:
            ref (int): the index of the reference atom
            mini (float): the inner radius of the shell
            maxi (float): the outer radius of the shell
        """

        indexes = atoms_in_shell.atoms_in_shell_box(self._variables['coordinates'],
                                                    ref,
                                                    mini,
                                                    maxi)
        
        atom_list = self._chemical_system.atom_list()

        selected_atoms = [atom_list[idx] for idx in indexes]

        return selected_atoms

    def contiguous_configuration(self):
        """Return a configuration with chemical entities made contiguous.

        Returns:
            MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration: the contiguous configuration
        """

        indexes = []
        for ce in self._chemical_system.chemical_entities:
            indexes.append([at.index for at in ce.atom_list()])

        contiguous_coords = contiguous_coordinates.contiguous_coordinates_box(
            self._variables['coordinates'],
            self._unit_cell.transposed_direct,
            indexes)

        conf = self
        conf._variables['coordinates'] = contiguous_coords
        return conf

    def contiguous_offsets(self,chemical_entities=None):
        """Returns the contiguity offsets for a list of chemical entities.

        Args:
            chemical_entities (list): the list of chemical entities

        Returns:
            ndarray: the offsets
        """

        if chemical_entities is None:
            chemical_entities = self._chemical_system.chemical_entities
        else:
            for ce in chemical_entities:
                if ce.root_chemical_system() is not self._chemical_system:
                    raise ConfigurationError('One or more chemical entities comes from another chemical system')

        indexes = []
        for ce in chemical_entities:
            indexes.append([at.index for at in ce.atom_list()])
        
        offsets = contiguous_coordinates.contiguous_offsets_box(
            self._variables['coordinates'],
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            indexes)

        return offsets

class PeriodicRealConfiguration(_PeriodicConfiguration):

    is_periodic = True

    def fold_coordinates(self):
        """Fold the coordinates into simulation box.
        """

        from MDANSE.Extensions import fold_coordinates

        coords = self._variables['coordinates']
        coords = coords[np.newaxis,:,:]
        unit_cell = self._unit_cell.transposed_direct
        inverse_unit_cell = self._unit_cell.transposed_inverse
        unit_cells = unit_cell[np.newaxis,:,:]
        inverse_unit_cells = inverse_unit_cell[np.newaxis,:,:]
        coords = fold_coordinates.fold_coordinates(
            coords,
            unit_cells,
            inverse_unit_cells,
            False
        )
        coords = np.squeeze(coords)
        self._variables['coordinates'] = coords

    def to_box_coordinates(self):
        """Return this configuration converted to box coordinates.

        Returns:
            ndarray: the box coordinates
        """

        return np.matmul(self._variables['coordinates'],self._unit_cell.inverse)

    def to_box_configuration(self):
        """Return this configuration converted to box coordinates.

        Returns:
            MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration: the configuration
        """

        coords = self.to_box_coordinates()

        variables = copy.deepcopy(self._variables)
        variables.pop('coordinates')

        box_conf = PeriodicBoxConfiguration(self._chemical_system,coords,self._unit_cell,**variables)

        return box_conf

    def to_real_coordinates(self):
        """Return the coordinates of this configuration converted to real coordinates.

        Returns:
            ndarray: the real coordinates
        """
        return self._variables['coordinates']

    def atomsInShell(self, ref, mini=0.0, maxi=10.0):
        """Returns the atoms found in a shell around a reference atom.

        Args:
            ref (int): the index of the reference atom
            mini (float): the inner radius of the shell
            maxi (float): the outer radius of the shell
        """

        indexes = atoms_in_shell.atoms_in_shell_real(
            self._variables['coordinates'],
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            ref,
            mini,
            maxi)

        atom_list = self._chemical_system.atom_list()

        selected_atoms = [atom_list[idx] for idx in indexes]

        return selected_atoms

    def contiguous_configuration(self):
        """Return a configuration with chemical entities made contiguous.

        Returns:
            MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration: the contiguous configuration
        """

        indexes = []
        for ce in self._chemical_system.chemical_entities:
            indexes.append([at.index for at in ce.atom_list()])

        contiguous_coords = contiguous_coordinates.contiguous_coordinates_real(
            self._variables['coordinates'],
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            indexes)

        conf = self
        conf._variables['coordinates'] = contiguous_coords
        return conf

    def continuous_configuration(self):
        """Return a configuration with chemical entities made continuous.

        Returns:
            MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration: the continuous configuration
        """

        contiguous_coords = contiguous_coordinates.continuous_coordinates(
            self._variables['coordinates'],
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            self._chemical_system)

        conf = self
        conf._variables['coordinates'] = contiguous_coords
        return conf

    def contiguous_offsets(self, chemical_entities=None):
        """Returns the contiguity offsets for a list of chemical entities.

        Args:
            chemical_entities (list): the list of chemical entities

        Returns:
            ndarray: the offsets
        """

        if chemical_entities is None:
            chemical_entities = self._chemical_system.chemical_entities
        else:
            for ce in chemical_entities:
                if ce.root_chemical_system() is not self._chemical_system:
                    raise ConfigurationError('One or more chemical entities comes from another chemical system')

        indexes = []
        for ce in chemical_entities:
            indexes.append([at.index for at in ce.atom_list()])
        
        offsets = contiguous_coordinates.contiguous_offsets_real(
            self._variables['coordinates'],
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            indexes)

        return offsets

class RealConfiguration(_Configuration):

    is_periodic = False

    def clone(self, chemical_system):
        """Clone this configuration.

        Args:
            chemical_system (MDANSE.Chemistry.ChemicalEntity.ChemicalSystem): the chemical system
        """

        if chemical_system.total_number_of_atoms() != self.chemical_system.total_number_of_atoms():
            raise ConfigurationError('Mismatch between the chemical systems')

        variables = copy.deepcopy(self.variables)

        coords = variables.pop('coordinates')

        return self.__class__(chemical_system,coords,**variables)        

    def fold_coordinates(self):
        """Fold the coordinates into simulation box.
        """
        return

    def to_real_coordinates(self):
        """Return the coordinates of this configuration converted to real coordinates.

        Returns:
            ndarray: the real coordinates
        """
        return self._variables['coordinates']

    def atomsInShell(self, ref, mini=0.0, maxi=10.0):
        """Returns the atoms found in a shell around a reference atom.

        Args:
            ref (int): the index of the reference atom
            mini (float): the inner radius of the shell
            maxi (float): the outer radius of the shell
        """

        indexes = atoms_in_shell.atoms_in_shell_nopbc(
            self._variables['coordinates'],
            ref,
            mini,
            maxi)

        atom_list = self._chemical_system.atom_list()

        selected_atoms = [atom_list[idx] for idx in indexes]

        return selected_atoms

    def contiguous_configuration(self):
        """Return a configuration with chemical entities made contiguous.

        Returns:
            MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration: the contiguous configuration
        """
        return self

    def continuous_configuration(self):
        """Return a configuration with chemical entities made continuous.

        Returns:
            MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration: the continuous configuration
        """
        return self

    def contiguous_offsets(self, chemical_entities=None):
        """Returns the contiguity offsets for a list of chemical entities.

        Args:
            chemical_entities (list): the list of chemical entities

        Returns:
            ndarray: the offsets
        """

        if chemical_entities is None:
            chemical_entities = self._chemical_system.chemical_entities
        else:
            for ce in chemical_entities:
                if ce.root_chemical_system() is not self._chemical_system:
                    raise ConfigurationError('One or more chemical entities comes from another chemical system')

        offsets = np.zeros((self._chemical_system.number_of_atoms(),3))

        return offsets

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

    uc = np.array([[10.0,0.0,0.0],[0.0,10.0,0.0],[0.0,0.0,10.0]])

    conf = RealConfiguration(cs, coordinates)

    print(conf.atomsInShell(0,0,5))






