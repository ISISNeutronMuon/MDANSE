#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import annotations
import abc
import copy
from typing import Union, TYPE_CHECKING

import numpy as np
from numpy.typing import ArrayLike

if TYPE_CHECKING:
    from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem, Atom, _ChemicalEntity
    from MDANSE.Mathematics.Transformation import RigidBodyTransformation
    from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.Extensions import atoms_in_shell, contiguous_coordinates


class ConfigurationError(Exception):
    pass


class _Configuration(metaclass=abc.ABCMeta):
    is_periodic: bool

    def __init__(self, chemical_system: ChemicalSystem, coords: ArrayLike, **variables):
        """
        Constructor.

        :param chemical_system: The chemical system described by this configuration.
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

        :param coords: the coordinates of all the particles in the chemical system
        :type coords: numpy.ndarray

        :param variables: keyword arguments for any other variables that should be saved to this configuration
        """

        self._chemical_system = chemical_system

        self._variables = {}

        self["coordinates"] = np.array(coords, dtype=float)

        for k, v in variables.items():
            if k == "velocities" or k == "forces":
                self[k] = np.array(v, dtype=float)
            else:
                self[k] = v

    def __contains__(self, item: str) -> bool:
        """
        Returns True if the provided variable belongs to the configuration.

        :param item: the variable to be confirmed
        :type item: str

        :return: True if the configuration has the given item, otherwise False
        :rtype: bool
        """
        return item in self._variables

    def __getitem__(self, item: str) -> np.ndarray:
        """
        Returns the configuration value for a given item.

        :param item: the variable whose value is to be retrieved
        :type item: str

        :return: the value of the variable
        """
        return self._variables[item]

    def __setitem__(self, name: str, value: ArrayLike) -> None:
        """
        Sets the provided variable to the provided value, but only if the value has the shape of
        (number of atoms in the chemical system, 3).

        :param name: the variable to be set
        :type name: str

        :param value: the value of the variable to be set
        :type value: numpy.ndarray
        """
        item = np.array(value)

        if name == "unit_cell":
            if item.shape != (3, 3):
                raise ValueError(
                    f"Invalid item dimensions for {name}; a shape of (3, 3) "
                    f"was expected but data with shape of {item.shape} was "
                    f"provided."
                )
            else:
                self._variables[name] = value
                return

        if item.shape != (self._chemical_system.number_of_atoms, 3):
            raise ValueError(
                f"Invalid item dimensions for {name}; a shape of {(self._chemical_system.number_of_atoms, 3)} was "
                f"expected but data with shape of {item.shape} was provided."
            )

        self._variables[name] = value

    def apply_transformation(self, transfo: RigidBodyTransformation) -> None:
        """
        Applies a linear transformation to the configuration.

        :param transfo: the transformation to be applied
        :type transfo: :class: `MDANSE.Mathematics.Transformation.RigidBodyTransformation`
        """
        conf = self["coordinates"]
        rot = transfo.rotation().tensor.array
        conf[:] = np.dot(conf, np.transpose(rot))

        np.add(
            conf,
            transfo.translation().vector.array[np.newaxis, :],
            conf,
            casting="unsafe",
        )

        if "velocities" in self._variables:
            velocities = self._variables["velocities"]
            rot = transfo.rotation().tensor.array
            velocities[:] = np.dot(velocities, np.transpose(rot))

    @property
    def chemical_system(self) -> ChemicalSystem:
        """
        Returns the chemical system stored in this configuration.

        :return: the chemical system that this configuration describes
        :rtype: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`
        """
        return self._chemical_system

    @abc.abstractmethod
    def clone(self, chemical_system: ChemicalSystem):
        """
        Clones this configuration.

        :param chemical_system: the chemical system that this configuration describes
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`
        """
        pass

    @property
    def coordinates(self) -> np.ndarray:
        """
        Returns the coordinates.

        :return: the coordinates stored in this configuration
        :rtype: numpy.ndarray
        """
        return self._variables["coordinates"]

    @abc.abstractmethod
    def to_real_coordinates(self):
        """
        Return the coordinates of this configuration converted to real coordinates.

        Returns:
            ndarray: the real coordinates
        """
        pass

    @property
    def variables(self) -> dict[str, np.ndarray]:
        """
        Returns the configuration variable dictionary.

        :return: all the variables stored in this configuration
        :rtype: dict
        """
        return self._variables


class _PeriodicConfiguration(_Configuration):
    def __init__(
        self,
        chemical_system: ChemicalSystem,
        coords: ArrayLike,
        unit_cell: UnitCell,
        **variables,
    ):
        """
        Constructor.

        :param chemical_system: The chemical system described by this configuration.
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

        :param coords: the coordinates of all the particles in the chemical system
        :type coords: numpy.ndarray

        :param unit_cell: the unit cell of the system in this configuration
        :type unit_cell: :class: `MDANSE.MolecularDynamics.UnitCell.UnitCell`

        :param variables: keyword arguments for any other variables that should be saved to this configuration
        """

        super(_PeriodicConfiguration, self).__init__(
            chemical_system, coords, **variables
        )

        if unit_cell.direct.shape != (3, 3):
            raise ValueError("Invalid unit cell dimensions")
        self._unit_cell = unit_cell

    def clone(self, chemical_system: Union[ChemicalSystem, None] = None):
        """
        Creates a deep copy of this configuration, using the provided chemical system.

        :param chemical_system: the chemical system that is to be used for copying. It must have the same number of
                                atoms as the chemical system that this configuration describes
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem):
        """
        if chemical_system is None:
            chemical_system = self._chemical_system
        else:
            if (
                chemical_system.total_number_of_atoms
                != self.chemical_system.total_number_of_atoms
            ):
                raise ConfigurationError(
                    "Mismatch between the chemical systems; the provided chemical system, "
                    f"{chemical_system.name}, has {chemical_system.total_number_of_atoms} atoms "
                    f"which does not match the chemical system of this configuration, "
                    f"{self.chemical_system.name} which has "
                    f"{self.chemical_system.total_number_of_atoms} atoms."
                )

        unit_cell = copy.deepcopy(self._unit_cell)

        variables = copy.deepcopy(self.variables)

        coords = variables.pop("coordinates")

        return self.__class__(chemical_system, coords, unit_cell, **variables)

    @abc.abstractmethod
    def fold_coordinates(self):
        """Fold the coordinates into simulation box."""
        pass

    @abc.abstractmethod
    def to_box_coordinates(self):
        """Return this configuration converted to box coordinates.

        Returns:
            ndarray: the box coordinates
        """
        pass

    @property
    def unit_cell(self) -> UnitCell:
        """
        Return the nit cell stored in this configuration.

        :return: the unit cell associated with this chemical system
        :rtype: :class: `MDANSE.MolecularDynamics.UnitCell.UnitCell
        """
        return self._unit_cell

    @unit_cell.setter
    def unit_cell(self, unit_cell: UnitCell) -> None:
        """
        Sets the unit cell.

        :param unit_cell: the new unit cell
        :type unit_cell: :class: `MDANSE.MolecularDynamics.UnitCell.UnitCell`
        """
        if unit_cell.direct.shape != (3, 3):
            raise ValueError("Invalid unit cell dimensions")
        self._unit_cell = unit_cell


class PeriodicBoxConfiguration(_PeriodicConfiguration):
    is_periodic = True

    def fold_coordinates(self) -> None:
        """Folds the coordinates into simulation box."""

        from MDANSE.Extensions import fold_coordinates

        coords = self._variables["coordinates"]
        coords = coords[np.newaxis, :, :]

        unit_cell = self._unit_cell.transposed_direct
        inverse_unit_cell = self._unit_cell.transposed_inverse

        unit_cells = unit_cell[np.newaxis, :, :]
        inverse_unit_cells = inverse_unit_cell[np.newaxis, :, :]

        coords = fold_coordinates.fold_coordinates(
            coords, unit_cells, inverse_unit_cells, True
        )
        coords = np.squeeze(coords)
        self._variables["coordinates"] = coords

    def to_box_coordinates(self) -> np.ndarray:
        """
        Return this configuration converted to box coordinates.

        :return: the box coordinates
        :rtype: numpy.ndarray
        """
        return self._variables["coordinates"]

    def to_real_coordinates(self) -> np.ndarray:
        """
        Return the coordinates of this configuration converted to real coordinates.

        :return: the real coordinates
        :rtype: numpy.ndarray
        """
        return np.matmul(self._variables["coordinates"], self._unit_cell.direct)

    def to_real_configuration(self) -> PeriodicRealConfiguration:
        """
        Return this configuration converted to real coordinates.

        :return: the configuration
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.PeriodicRealConfiguration`
        """

        coords = self.to_real_coordinates()

        variables = copy.deepcopy(self._variables)
        variables.pop("coordinates")

        real_conf = PeriodicRealConfiguration(
            self._chemical_system, coords, self._unit_cell, **variables
        )

        return real_conf

    def atoms_in_shell(
        self, ref: int, mini: float = 0.0, maxi: float = 10.0
    ) -> list[Atom]:
        """
        Returns all atoms found in a shell around a reference atom. The shell is a (hollow) sphere around the reference
        atom defined by parameters mini and maxi. All atoms within the sphere with radius maxi but not within that of
        radius mini are returned. Atoms that are exactly mini or maxi distance away from the reference atom ARE counted
        For more details, see :func: `MDANSE.Extensions.atoms_in_shell.atoms_in_shell_box`, which is called under the
        hood.

        :param ref: the index of the reference atom
        :type ref: int

        :param mini: the inner radius of the shell
        :type mini: float

        :param maxi: the outer radius of the shell
        :type maxi: float

        :return: list of atoms within the defined shell
        :rtype: list
        """

        indexes = atoms_in_shell.atoms_in_shell_box(
            self._variables["coordinates"].astype(np.float64), ref, mini, maxi
        )

        atom_list = self._chemical_system.atom_list

        selected_atoms = [atom_list[idx] for idx in indexes]

        return selected_atoms

    def contiguous_configuration(self) -> PeriodicBoxConfiguration:
        """
        Return a configuration with chemical entities made contiguous.

        :return: the contiguous configuration
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration`
        """

        indexes = []
        for ce in self._chemical_system.chemical_entities:
            indexes.append([at.index for at in ce.atom_list])

        contiguous_coords = contiguous_coordinates.contiguous_coordinates_box(
            self._variables["coordinates"], self._unit_cell.transposed_direct, indexes
        )

        conf = self.clone()
        conf._variables["coordinates"] = contiguous_coords
        return conf

    def contiguous_offsets(
        self, chemical_entities: list[_ChemicalEntity] = None
    ) -> np.ndarray:
        """
        Returns the contiguity offsets for a list of chemical entities.

        :param chemical_entities: the list of chemical entities whose offsets are to be calculated or None for all
                                  entities in the chemical system
        :type chemical_entities: list

        :return: the offsets
        :rtype: numpy.ndarray
        """

        if chemical_entities is None:
            chemical_entities = self._chemical_system.chemical_entities
        else:
            for i, ce in enumerate(chemical_entities):
                root = ce.root_chemical_system
                if root is not self._chemical_system:
                    raise ConfigurationError(
                        "All the entities provided in the chemical_entities parameter must belong "
                        "to the chemical system registered with this configuration, which is "
                        f"{self._chemical_system.name}. However, the entity at index {i}, "
                        f"{str(ce)}, is in chemical system "
                        f"{root.name if root is not None else None}.\nExpected chemical system: "
                        f"{repr(self._chemical_system)}\nActual chemical system: {repr(root)}\n"
                        f"Faulty chemical entity: {repr(ce)}"
                    )

        indexes = []
        for ce in chemical_entities:
            indexes.append([at.index for at in ce.atom_list])

        offsets = contiguous_coordinates.contiguous_offsets_box(
            self._variables["coordinates"][
                [item for sublist in indexes for item in sublist]
            ],
            self._unit_cell.transposed_direct,
            indexes,
        )

        return offsets


class PeriodicRealConfiguration(_PeriodicConfiguration):
    is_periodic = True

    def fold_coordinates(self) -> None:
        """Fold the coordinates into simulation box."""

        from MDANSE.Extensions import fold_coordinates

        coords = self._variables["coordinates"]
        coords = coords[np.newaxis, :, :]

        unit_cell = self._unit_cell.transposed_direct
        inverse_unit_cell = self._unit_cell.transposed_inverse

        unit_cells = unit_cell[np.newaxis, :, :]
        inverse_unit_cells = inverse_unit_cell[np.newaxis, :, :]

        coords = fold_coordinates.fold_coordinates(
            coords, unit_cells, inverse_unit_cells, False
        )
        coords = np.squeeze(coords)

        self._variables["coordinates"] = coords

    def to_box_coordinates(self) -> np.ndarray:
        """
        Returns the (real) coordinates stored in this configuration converted into box coordinates.

        :return: box coordinates
        :rtype: numpy.ndarray
        """

        return np.matmul(self._variables["coordinates"], self._unit_cell.inverse)

    def to_box_configuration(self) -> PeriodicBoxConfiguration:
        """
        Creates a copy of this configuration with its coordinates converted into box coordinates.

        :return: a configuration with all parameters the same except for coordinates which are box instead of real
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration`
        """

        coords = self.to_box_coordinates()

        variables = copy.deepcopy(self._variables)
        variables.pop("coordinates")

        box_conf = PeriodicBoxConfiguration(
            self._chemical_system, coords, self._unit_cell, **variables
        )

        return box_conf

    def to_real_coordinates(self) -> np.ndarray:
        """
        Return the coordinates of this configuration converted to real coordinates, i.e. the coordinates registered with
        this configuration.

        :return: the real coordinates
        :rtype: numpy.ndarray
        """
        return self._variables["coordinates"]

    def atoms_in_shell(
        self, ref: int, mini: float = 0.0, maxi: float = 10.0
    ) -> list[Atom]:
        """
        Returns all atoms found in a shell around a reference atom. The shell is a (hollow) sphere around the reference
        atom defined by parameters mini and maxi. All atoms within the sphere with radius maxi but not within that of
        radius mini are returned. Atoms that are exactly mini or maxi distance away from the reference atom ARE counted
        For more details, see :func: `MDANSE.Extensions.atoms_in_shell.atoms_in_shell_real`, which is called under the
        hood.

        :param ref: the index of the reference atom
        :type ref: int

        :param mini: the inner radius of the shell
        :type mini: float

        :param maxi: the outer radius of the shell
        :type maxi: float

        :return: list of atoms within the defined shell
        :rtype: list
        """

        indexes = atoms_in_shell.atoms_in_shell_real(
            self._variables["coordinates"].astype(np.float64),
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            ref,
            mini,
            maxi,
        )

        atom_list = self._chemical_system.atom_list

        selected_atoms = [atom_list[idx] for idx in indexes]

        return selected_atoms

    def contiguous_configuration(self) -> PeriodicRealConfiguration:
        """
        Return a configuration with chemical entities made contiguous.

        :return: the contiguous configuration
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration`
        """

        indexes = []
        for ce in self._chemical_system.chemical_entities:
            indexes.append([at.index for at in ce.atom_list])

        contiguous_coords = contiguous_coordinates.contiguous_coordinates_real(
            self._variables["coordinates"],
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            indexes,
        )

        conf = self.clone()
        conf._variables["coordinates"] = contiguous_coords
        return conf

    def continuous_configuration(self) -> PeriodicRealConfiguration:
        """
        Return a configuration with chemical entities made continuous.

        :return:  the continuous configuration
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration`
        """

        contiguous_coords = contiguous_coordinates.continuous_coordinates(
            self._variables["coordinates"],
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            self._chemical_system,
        )

        conf = self.clone()
        conf._variables["coordinates"] = contiguous_coords
        return conf

    def contiguous_offsets(
        self, chemical_entities: Union[None, list[_ChemicalEntity]] = None
    ) -> np.ndarray:
        """
        Returns the contiguity offsets for a list of chemical entities.

        :param chemical_entities: the list of chemical entities whose offsets are to be calculated or None for all
                                  entities in the chemical system
        :type chemical_entities: list

        :return: the offsets
        :rtype: numpy.ndarray
        """

        if chemical_entities is None:
            chemical_entities = self._chemical_system.chemical_entities
        else:
            for i, ce in enumerate(chemical_entities):
                root = ce.root_chemical_system
                if root is not self._chemical_system:
                    raise ConfigurationError(
                        "All the entities provided in the chemical_entities parameter must belong "
                        "to the chemical system registered with this configuration, which is "
                        f"{self._chemical_system.name}. However, the entity at index {i}, "
                        f"{str(ce)}, is in chemical system "
                        f"{root.name if root is not None else None}.\nExpected chemical system: "
                        f"{repr(self._chemical_system)}\nActual chemical system: {repr(root)}\n"
                        f"Faulty chemical entity: {repr(ce)}"
                    )
        indexes = []
        for ce in chemical_entities:
            indexes.append([at.index for at in ce.atom_list])

        offsets = contiguous_coordinates.contiguous_offsets_real(
            self._variables["coordinates"][
                [item for sublist in indexes for item in sublist]
            ],
            self._unit_cell.transposed_direct,
            self._unit_cell.transposed_inverse,
            indexes,
        )

        return offsets


class RealConfiguration(_Configuration):
    is_periodic = False

    def clone(
        self, chemical_system: Union[None, ChemicalSystem] = None
    ) -> RealConfiguration:
        """
        Creates a deep copy of this configuration, using the provided chemical system.

        :param chemical_system: the chemical system that is to be used for copying. It must have the same number of
                                atoms as the chemical system that this configuration describes
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalEntity.ChemicalSystem`

        :return: the cloned configuration
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.RealConfiguration`
        """
        if chemical_system is None:
            chemical_system = self._chemical_system
        else:
            if (
                chemical_system.total_number_of_atoms
                != self.chemical_system.total_number_of_atoms
            ):
                raise ConfigurationError("Mismatch between the chemical systems")

        variables = copy.deepcopy(self.variables)

        coords = variables.pop("coordinates")

        return self.__class__(chemical_system, coords, **variables)

    def fold_coordinates(self) -> None:
        """Does nothing since coordinates can only be folded if the configuration has a unit cell."""
        return

    def to_real_coordinates(self) -> np.ndarray:
        """
        Return the coordinates of this configuration converted to real coordinates.

        :return: the real coordinates
        :rtype: numpy.ndarray
        """
        return self._variables["coordinates"]

    def atoms_in_shell(
        self, ref: int, mini: float = 0.0, maxi: float = 10.0
    ) -> list[Atom]:
        """
        Returns all atoms found in a shell around a reference atom. The shell is a (hollow) sphere around the reference
        atom defined by parameters mini and maxi. All atoms within the sphere with radius maxi but not within that of
        radius mini are returned. Atoms that are exactly mini or maxi distance away from the reference atom ARE counted
        For more details, see :func: `MDANSE.Extensions.atoms_in_shell.atoms_in_shell_nopbc`, which is called under the
        hood.

        :param ref: the index of the reference atom
        :type ref: int

        :param mini: the inner radius of the shell
        :type mini: float

        :param maxi: the outer radius of the shell
        :type maxi: float

        :return: list of atoms within the defined shell
        :rtype: list
        """

        indexes = atoms_in_shell.atoms_in_shell_nopbc(
            self._variables["coordinates"].astype(np.float64), ref, mini, maxi
        )

        atom_list = self._chemical_system.atom_list

        selected_atoms = [atom_list[idx] for idx in indexes]

        return selected_atoms

    def contiguous_configuration(self) -> RealConfiguration:
        """
        Return a configuration with chemical entities made contiguous, which is always itself.

        :return: itself
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.RealConfiguration`
        """
        return self

    def continuous_configuration(self) -> RealConfiguration:
        """
        Return a configuration with chemical entities made continuous, which is always itself.

        :return: itself
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.RealConfiguration`
        """
        return self

    def contiguous_offsets(
        self, chemical_entities: Union[None, list[_ChemicalEntity]] = None
    ) -> np.ndarray:
        """
        Returns the contiguity offsets for a list of chemical entities, which are always zero for every atom.

        :param chemical_entities: the list of chemical entities whose offsets are to be calculated or None for all
                                  entities in the chemical system
        :type chemical_entities: list

        :return: the offsets
        :rtype: numpy.ndarray
        """

        if chemical_entities is None:
            chemical_entities = self._chemical_system.chemical_entities
        else:
            for j, ce in enumerate(chemical_entities):
                root = ce.root_chemical_system
                if root is not self._chemical_system:
                    raise ConfigurationError(
                        "All the entities provided in the chemical_entities parameter must belong "
                        "to the chemical system registered with this configuration, which is "
                        f"{self._chemical_system.name}. However, the entity at index {j}, "
                        f"{str(ce)}, is in chemical system "
                        f"{root.name if root is not None else None}.\nExpected chemical system: "
                        f"{repr(self._chemical_system)}\nActual chemical system: {repr(root)}\n"
                        f"Faulty chemical entity: {repr(ce)}"
                    )

        number_of_particles = sum(
            [ce.total_number_of_atoms for ce in chemical_entities]
        )

        offsets = np.zeros((number_of_particles, 3))

        return offsets


if __name__ == "__main__":
    np.random.seed(1)

    from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem

    n_atoms = 2
    cs = ChemicalSystem()
    for i in range(n_atoms):
        cs.add_chemical_entity(Atom(symbol="H"))

    coordinates = np.empty((n_atoms, 3), dtype=float)
    coordinates[0, :] = [1, 1, 1]
    coordinates[1, :] = [3, 3, 3]

    uc = np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]])

    conf = RealConfiguration(cs, coordinates)

    print(conf.atoms_in_shell(0, 0, 5))
