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
from functools import reduce
from typing import TYPE_CHECKING

import networkx as nx
import numpy as np
from numpy.typing import ArrayLike

if TYPE_CHECKING:
    from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
    from MDANSE.Mathematics.Transformation import RigidBodyTransformation
    from MDANSE.MolecularDynamics.UnitCell import UnitCell


def remove_jumps(input_coords: np.ndarray) -> np.ndarray:
    """Takes a series of particle positions in time
    and makes the motion continuous by removing any jumps across
    the simulation box boundary.

    Parameters
    ----------
    input_coords : np.ndarray
        An (n_time_steps, 3) array of FRACTIONAL atom coordinates

    Returns
    -------
    np.ndarray
        The same array of atom positions, corrected for jumps by 1
        full box length
    """
    steps = np.round(input_coords[1:] - input_coords[:-1]).astype(int)
    offsets = np.zeros_like(input_coords)
    for axis_index in range(3):
        changes = np.argwhere(steps[:, axis_index])
        for time_step_with_jump in changes:
            try:
                time_index = time_step_with_jump[0]
            except IndexError:
                continue
            offsets[time_index + 1 :, axis_index] -= steps[time_index, axis_index]
    return input_coords + offsets


def contiguous_coordinates_real(
    coords: np.ndarray,
    cell: np.ndarray,
    rcell: np.ndarray,
    indices: list[tuple[int, ...]],
    bring_to_centre: bool = False,
):
    """Translates atoms by a lattice vector. Returns a coordinate array
    in which atoms in each segment are separated from the first atom
    by less than half the simulation box length.

    Parameters
    ----------
    coords : np.ndarray
        Array of atom coordinates
    cell : np.ndarray
        3x3 unit cell array
    rcell : np.ndarray
        3x3 reciprocal cell array
    indices : List[Tuple[int]]
        a list of index group, as in [[1,2,3], [7,8]]
        (this would ensure 2 and 3 are close to 1, and 8 is close to 7)
    bring_to_centre: bool
        if true, atoms are shifted to minimise the distance from the average
        position and not from the first atom

    Returns
    -------
    np.ndarray
        new coordinate array with the translations applied
    """

    contiguous_coords = coords.copy()

    scaleconfig = np.matmul(coords, rcell)

    for idxs in indices:
        if len(idxs) < 2:
            continue
        if bring_to_centre:
            centre = np.mean(scaleconfig[idxs], axis=0)
            minimum_offsets = scaleconfig[idxs] - centre
            minimum_offsets -= np.round(minimum_offsets)
            newconfig = centre + minimum_offsets
            newconfig = np.matmul(newconfig, cell)
            contiguous_coords[idxs] = newconfig
        else:
            minimum_offsets = scaleconfig[idxs[1:]] - scaleconfig[idxs[0]]
            minimum_offsets -= np.round(minimum_offsets)
            newconfig = scaleconfig[idxs[0]] + minimum_offsets
            newconfig = np.matmul(newconfig, cell)
            contiguous_coords[idxs[1:]] = newconfig

    return contiguous_coords


def contiguous_coordinates_box(
    frac_coords: np.ndarray,
    indices: list[tuple[int, ...]],
    bring_to_centre: bool = False,
):
    """Translates atoms by a lattice vector. Returns a FRACTIONAL coordinate array
    in which atoms in each segment are separated from the first atom
    by less than half the simulation box length.

    Parameters
    ----------
    coords : np.ndarray
        Array of fractional coordinates
    cell : np.ndarray
        3x3 unit cell array
    indices : List[Tuple[int]]
        a list of index group, as in [[1,2,3], [7,8]]
        (this would ensure 2 and 3 are close to 1, and 8 is close to 7)
    bring_to_centre: bool
        if true, atoms are shifted to minimise the distance from the average
        position and not from the first atom

    Returns
    -------
    np.ndarray
        array of atom coordinates with the translations applied
    """

    contiguous_coords = frac_coords.copy()

    for tupleidxs in indices:
        if len(tupleidxs) < 2:
            continue

        idxs = list(tupleidxs)
        if bring_to_centre:
            centre = np.mean(frac_coords[idxs], axis=0)
            sdx = frac_coords[idxs] - centre
            sdx -= np.round(sdx)
            contiguous_coords[idxs] = frac_coords[idxs] + sdx
        else:
            sdx = frac_coords[idxs[1:]] - frac_coords[idxs[0]]
            sdx -= np.round(sdx)
            contiguous_coords[idxs[1:]] = frac_coords[idxs[0]] + sdx

    return contiguous_coords


def continuous_coordinates(
    coords: np.ndarray,
    cell: np.ndarray,
    rcell: np.ndarray,
    bond_list: list[tuple[int, ...]],
):
    """Translates atoms by lattice vectors to ensure that
    no bonds are broken. Does nothing if no bonds are defined
    in the system.

    Parameters
    ----------
    coords : np.ndarray
        Array of atom coordinates
    cell : np.ndarray
        3x3 unit cell array
    rcell : np.ndarray
        3x3 reciprocal cell array
    bond_list : List[Tuple[int]]
        List of bonds in the system

    Returns
    -------
    np.ndarray
        new array of atom coordinates with translations applied
    """
    atom_pool = list(range(len(coords)))
    total_graph = nx.Graph()
    total_graph.add_nodes_from(atom_pool)
    total_graph.add_edges_from(bond_list)
    segments = []
    while len(atom_pool) > 0:
        last_atom = atom_pool.pop()
        temp_dict = nx.dfs_successors(total_graph, last_atom)
        others = reduce(list.__add__, temp_dict.values(), [])
        for atom in others:
            atom_pool.pop(atom_pool.index(atom))
        segment = [last_atom] + others
        segments.append(sorted(segment))
    return contiguous_coordinates_real(coords, cell, rcell, segments)


def padded_coordinates(
    coords: np.ndarray,
    unit_cell: UnitCell,
    thickness: float,
    fold_into_box: bool = True,
) -> np.ndarray:
    """Repeats coordinates in copies of the unit cell, and removes
    the atoms that are now within the specified distance from the cell wall.
    The returned coordinate array contains all the original atoms,
    and additionally the atoms from the copies within the thickness
    from the original cell walls.

    Parameters
    ----------
    coords : np.ndarray
        Array of all the atoms in the unit cell
    unit_cell : UnitCell
        an instance of the UnitCell class, defining the simulation box
    thickness : float
        thickness of the outer layer to be included
    fold_into_box : bool
        if True, translates all the atoms so their fractional coordinates are in [0.0, 1.0)

    Returns
    -------
    np.ndarray
        Array of atom coordinates, together with their copies

    Raises
    ------
    VoronoiError
        Any error that may indicate that a Voronoi job failed
    """
    if abs(thickness) < 1e-6:
        return coords, np.arange(len(coords), dtype=int)
    vectors = (
        unit_cell.a_vector,
        unit_cell.b_vector,
        unit_cell.c_vector,
    )
    fractional_lengths = [thickness / np.linalg.norm(vector) for vector in vectors]
    all_indices = np.arange(len(coords), dtype=int)
    for axis in range(3):
        extra_arrays = []
        extra_indices = []
        cutoff_max = 1 + fractional_lengths[axis]
        cutoff_min = -fractional_lengths[axis]
        for shift in [-1, 1]:
            offset = vectors[axis] * shift
            new_points = coords + offset.reshape((1, 3))
            frac_points = np.matmul(new_points, unit_cell.inverse)
            if fold_into_box:
                frac_points -= np.floor(frac_points)
            if shift > 0:
                criterion = np.where(frac_points[:, axis] < cutoff_max)
                new_points = new_points[criterion]
                new_indices = all_indices[criterion]
            else:
                criterion = np.where(frac_points[:, axis] > cutoff_min)
                new_points = new_points[criterion]
                new_indices = all_indices[criterion]
            if len(new_points) > 0:
                extra_arrays.append(new_points)
                extra_indices.append(new_indices)
        if len(extra_arrays) > 0:
            coords = np.vstack([coords] + extra_arrays)
            all_indices = np.concatenate([all_indices] + extra_indices)
    return coords, all_indices


class ConfigurationError(Exception):
    pass


class _Configuration(metaclass=abc.ABCMeta):
    is_periodic: bool

    def __init__(self, chemical_system: ChemicalSystem, coords: ArrayLike, **variables):
        """
        Constructor.

        :param chemical_system: The chemical system described by this configuration.
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalSystem.ChemicalSystem`

        :param coords: the coordinates of all the particles in the chemical system
        :type coords: numpy.ndarray

        :param variables: keyword arguments for any other variables that should be saved to this configuration
        """

        self._chemical_system = chemical_system

        self._variables = {}

        self["coordinates"] = np.array(coords, dtype=float)

        for k, v in variables.items():
            if k in {"velocities", "forces"}:
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
        :rtype: :class: `MDANSE.Chemistry.ChemicalSystem.ChemicalSystem`
        """
        return self._chemical_system

    @abc.abstractmethod
    def clone(self, chemical_system: ChemicalSystem):
        """
        Clones this configuration.

        :param chemical_system: the chemical system that this configuration describes
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalSystem.ChemicalSystem`
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
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalSystem.ChemicalSystem`

        :param coords: the coordinates of all the particles in the chemical system
        :type coords: numpy.ndarray

        :param unit_cell: the unit cell of the system in this configuration
        :type unit_cell: :class: `MDANSE.MolecularDynamics.UnitCell.UnitCell`

        :param variables: keyword arguments for any other variables that should be saved to this configuration
        """

        super().__init__(chemical_system, coords, **variables)

        if unit_cell.direct.shape != (3, 3):
            raise ValueError("Invalid unit cell dimensions")
        self._unit_cell = unit_cell

    def clone(self, chemical_system: ChemicalSystem | None = None):
        """
        Creates a deep copy of this configuration, using the provided chemical system.

        :param chemical_system: the chemical system that is to be used for copying. It must have the same number of
                                atoms as the chemical system that this configuration describes
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalSystem.ChemicalSystem):
        """
        if chemical_system is None:
            chemical_system = self._chemical_system
        elif (
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

    def fold_coordinates(self):
        """Fold the coordinates into simulation box."""
        coords = self._variables["coordinates"]

        unit_cell = self._unit_cell.direct
        inverse_unit_cell = self._unit_cell.inverse

        self._variables["coordinates"] = (coords @ inverse_unit_cell % 1) @ unit_cell

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

    def contiguous_configuration(
        self, bring_to_centre: bool = False
    ) -> PeriodicBoxConfiguration:
        """
        Return a configuration with chemical entities made contiguous.

        :return: the contiguous configuration
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration`
        """

        indices_grouped = reduce(
            list.__add__, self._chemical_system._clusters.values(), []
        )

        contiguous_coords = contiguous_coordinates_box(
            self._variables["coordinates"],
            indices_grouped,
            bring_to_centre,
        )

        conf = self.clone()
        conf._variables["coordinates"] = contiguous_coords
        return conf


class PeriodicRealConfiguration(_PeriodicConfiguration):
    is_periodic = True

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

    def contiguous_configuration(
        self, bring_to_centre: bool = False
    ) -> PeriodicRealConfiguration:
        """
        Return a configuration with chemical entities made contiguous.

        :return: the contiguous configuration
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.PeriodicBoxConfiguration`
        """

        indices_grouped = reduce(
            list.__add__, self._chemical_system._clusters.values(), []
        )

        contiguous_coords = contiguous_coordinates_real(
            self._variables["coordinates"],
            self._unit_cell.direct,
            self._unit_cell.inverse,
            indices_grouped,
            bring_to_centre,
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

        continuous_coords = continuous_coordinates(
            self._variables["coordinates"],
            self._unit_cell.direct,
            self._unit_cell.inverse,
            self.chemical_system._bonds,
        )

        conf = self.clone()
        conf._variables["coordinates"] = continuous_coords
        return conf


class RealConfiguration(_Configuration):
    is_periodic = False

    def clone(self, chemical_system: ChemicalSystem | None = None) -> RealConfiguration:
        """
        Creates a deep copy of this configuration, using the provided chemical system.

        :param chemical_system: the chemical system that is to be used for copying. It must have the same number of
                                atoms as the chemical system that this configuration describes
        :type chemical_system: :class: `MDANSE.Chemistry.ChemicalSystem.ChemicalSystem`

        :return: the cloned configuration
        :rtype: :class: `MDANSE.MolecularDynamics.Configuration.RealConfiguration`
        """
        if chemical_system is None:
            chemical_system = self._chemical_system
        elif (
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

    def contiguous_configuration(
        self, bring_to_centre: bool = False
    ) -> RealConfiguration:
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


if __name__ == "__main__":
    np.random.seed(1)

    n_atoms = 2
    cs = ChemicalSystem()
    cs.initialise_atoms(["H", "H"])

    coordinates = np.empty((n_atoms, 3), dtype=float)
    coordinates[0, :] = [1, 1, 1]
    coordinates[1, :] = [3, 3, 3]

    uc = np.array([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]])

    conf = RealConfiguration(cs, coordinates)
