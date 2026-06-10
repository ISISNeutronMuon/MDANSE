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
from collections.abc import Sequence
from functools import reduce
from typing import TYPE_CHECKING, Any

import networkx as nx
import numpy as np

from MDANSE.MLogging import LOG
from MDANSE.util_types import FloatArray, IntArray

if TYPE_CHECKING:
    from numpy.typing import ArrayLike

    from MDANSE.MolecularDynamics.UnitCell import UnitCell


def remove_jumps(input_coords: FloatArray) -> FloatArray:
    """Takes a series of particle positions in time
    and makes the motion continuous by removing any jumps across
    the simulation box boundary.

    Parameters
    ----------
    input_coords : FloatArray
        An (n_time_steps, 3) array of FRACTIONAL atom coordinates

    Returns
    -------
    FloatArray
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


def contiguous_coordinates_absolute(
    coords: FloatArray,
    cell: FloatArray,
    rcell: FloatArray,
    indices: list[tuple[int, ...]],
    bring_to_centre: bool = False,
) -> FloatArray:
    """Translates atoms by a lattice vector. Returns a coordinate array
    in which atoms in each segment are separated from the first atom
    by less than half the simulation box length.

    Parameters
    ----------
    coords : FloatArray
        Array of atom coordinates
    cell : FloatArray
        3x3 unit cell array
    rcell : FloatArray
        3x3 reciprocal cell array
    indices : List[Tuple[int]]
        a list of index group, as in [[1,2,3], [7,8]]
        (this would ensure 2 and 3 are close to 1, and 8 is close to 7)
    bring_to_centre: bool
        if true, atoms are shifted to minimise the distance from the average
        position and not from the first atom

    Returns
    -------
    FloatArray
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


def contiguous_coordinates_fractional(
    frac_coords: FloatArray,
    indices: list[tuple[int, ...]],
    bring_to_centre: bool = False,
) -> FloatArray:
    """Translates atoms by a lattice vector. Returns a FRACTIONAL coordinate array
    in which atoms in each segment are separated from the first atom
    by less than half the simulation box length.

    Parameters
    ----------
    coords : FloatArray
        Array of fractional coordinates
    cell : FloatArray
        3x3 unit cell array
    indices : List[Tuple[int]]
        a list of index group, as in [[1,2,3], [7,8]]
        (this would ensure 2 and 3 are close to 1, and 8 is close to 7)
    bring_to_centre: bool
        if true, atoms are shifted to minimise the distance from the average
        position and not from the first atom

    Returns
    -------
    FloatArray
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
    coords: FloatArray,
    cell: FloatArray,
    rcell: FloatArray,
    bond_list: list[tuple[int, ...]],
):
    """Translates atoms by lattice vectors to ensure that
    no bonds are broken. Does nothing if no bonds are defined
    in the system.

    Parameters
    ----------
    coords : FloatArray
        Array of atom coordinates
    cell : FloatArray
        3x3 unit cell array
    rcell : FloatArray
        3x3 reciprocal cell array
    bond_list : List[Tuple[int]]
        List of bonds in the system

    Returns
    -------
    FloatArray
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
        segment = [last_atom, *others]
        segments.append(sorted(segment))
    return contiguous_coordinates_absolute(coords, cell, rcell, segments)


def padded_coordinates(
    coords: FloatArray,
    unit_cell: UnitCell | None,
    thickness: float,
    fold_into_box: bool = True,
) -> tuple[FloatArray, IntArray]:
    """Repeats coordinates in copies of the unit cell, and removes
    the atoms that are now within the specified distance from the cell wall.
    The returned coordinate array contains all the original atoms,
    and additionally the atoms from the copies within the thickness
    from the original cell walls.

    Parameters
    ----------
    coords : FloatArray
        Array of all the atoms in the unit cell
    unit_cell : UnitCell
        an instance of the UnitCell class, defining the simulation box
    thickness : float
        thickness of the outer layer to be included
    fold_into_box : bool
        if True, translates all the atoms so their fractional coordinates are in [0.0, 1.0)

    Returns
    -------
    tuple[FloatArray, IntArray]
        Array of atom coordinates, together with their copies

    Raises
    ------
    VoronoiError
        Any error that may indicate that a Voronoi job failed
    """
    if abs(thickness) < 1e-6:
        return coords, np.arange(len(coords), dtype=int)
    if unit_cell is None:
        LOG.warning(
            "No unit cell given to padded_coordinates, but padding of %s was requested",
            thickness,
        )
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
            coords = np.vstack([coords, *extra_arrays])
            all_indices = np.concatenate([all_indices, *extra_indices])
    return coords, all_indices


class ConfigurationError(Exception):
    pass


class _Configuration(metaclass=abc.ABCMeta):
    is_periodic: bool

    def __init__(self, coords: ArrayLike, **variables):

        self._variables = {}

        self["coordinates"] = np.array(coords, dtype=float)
        self._n_atoms = len(self["coordinates"])

        for k, v in variables.items():
            if k in {"velocities", "forces"}:
                self[k] = np.array(v, dtype=float)
            else:
                self[k] = v

    def __contains__(self, item: str) -> bool:
        """Check if a variable is stored in this configuration.

        Parameters
        ----------
        item : str
            Name of the atom property array.

        Returns
        -------
        bool
            True if 'item' is the configuration's variables, False otherwise.
        """
        return item in self._variables

    def __getitem__(self, item: str) -> FloatArray:
        """Return the selected atom property array.

        Parameters
        ----------
        item : str
            Name of the array, e.g. 'velocities'

        Returns
        -------
        np.ndarray
            An (N_ATOMS, 3) data array.
        """
        return self._variables[item]

    def __setitem__(self, name: str, value: ArrayLike) -> None:
        """Store a data array in this Configuration instance.

        Parameters
        ----------
        name : str
            Key under which the array will be stored.
        value : ArrayLike
            Input data array.

        Raises
        ------
        ValueError
            If the unit cell array is not a (3, 3) array.
        ValueError
            If the shape of the array does not match the number of atoms.
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

        if any(
            item.shape != existing_item.shape
            for existing_item in self._variables.values()
        ):
            raise ValueError(
                f"Invalid item dimensions for {name}; a shape of {(self._n_atoms, 3)} was "
                f"expected but data with shape of {item.shape} was provided."
            )

        self._variables[name] = value

    @abc.abstractmethod
    def clone(self):
        """Return a copy of this configuration."""
        pass

    @property
    def coordinates(self) -> FloatArray:
        """The array of atom coordinates."""
        return self._variables["coordinates"]

    @abc.abstractmethod
    def to_absolute_coordinates(self):
        """Return the atom positions as absolute coordinates."""
        pass

    @property
    def variables(self) -> dict[str, FloatArray]:
        """Return all atom data arrays in a dictionary.

        Returns
        -------
        dict[str, np.ndarray]
            Dictionary containing atom positions (optionally also velocities, ...)
        """
        return self._variables


class _PeriodicConfiguration(_Configuration):
    """Class storing atom positions with periodic boundary conditions."""

    def __init__(
        self,
        coords: ArrayLike,
        unit_cell: UnitCell,
        **variables,
    ):
        super().__init__(coords, **variables)

        if unit_cell.direct.shape != (3, 3):
            raise ValueError("Invalid unit cell dimensions")
        self._unit_cell = unit_cell

    def clone(self) -> _PeriodicConfiguration:
        """Return a deep copy of this configuration."""

        unit_cell = copy.deepcopy(self._unit_cell)
        variables = copy.deepcopy(self.variables)
        coords = variables.pop("coordinates")

        return type(self)(coords, unit_cell, **variables)

    def fold_coordinates(self):
        """Fold the coordinates into simulation box."""
        coords = self._variables["coordinates"]

        unit_cell = self._unit_cell.direct
        inverse_unit_cell = self._unit_cell.inverse

        self._variables["coordinates"] = (coords @ inverse_unit_cell % 1) @ unit_cell

    @abc.abstractmethod
    def to_fractional_coordinates(self):
        """Return this configuration converted to fractional coordinates."""
        pass

    @property
    def unit_cell(self) -> UnitCell:
        """Return the unit cell of this configuration.

        Returns
        -------
        UnitCell
            A unit cell with the current simulation box dimensions.
        """
        return self._unit_cell

    @unit_cell.setter
    def unit_cell(self, unit_cell: UnitCell) -> None:
        """Replace the unit cell of the configuration with the input one.

        Parameters
        ----------
        unit_cell : UnitCell
            Unit cell instance with the dimensions of the simulation box.

        Raises
        ------
        ValueError
            If the unit cell does not contain a valid (3, 3) cell array.
        """
        if unit_cell.direct.shape != (3, 3):
            raise ValueError("Invalid unit cell dimensions")
        self._unit_cell = unit_cell


class PeriodicFractionalConfiguration(_PeriodicConfiguration):
    is_periodic = True

    def to_fractional_coordinates(self) -> FloatArray:
        """Return atom positions as fractional coordinates."""
        return self._variables["coordinates"]

    def to_absolute_coordinates(self) -> FloatArray:
        """Return atom positions as absolute coordinates."""
        return np.matmul(self._variables["coordinates"], self._unit_cell.direct)

    def to_absolute_configuration(self) -> PeriodicAbsoluteConfiguration:
        """Return atom positions as absolute coordinates in a configuration instance."""

        coords = self.to_absolute_coordinates()

        variables = copy.deepcopy(self._variables)
        variables.pop("coordinates")

        real_conf = PeriodicAbsoluteConfiguration(coords, self._unit_cell, **variables)

        return real_conf

    def contiguous_configuration(
        self, indices_grouped: Sequence[Sequence[int]], bring_to_centre: bool = False
    ) -> PeriodicFractionalConfiguration:
        """Return a configuration with contiguous coordinates.

        Atoms will be moved by unit cell vectors to minimise the distance
        between atoms belonging to groups defined in the input list.

        Parameters
        ----------
        indices_grouped : Sequence[Sequence[int]]
            List containing a list of atom indices for every molecule in the system.
        bring_to_centre : bool, optional
            If True, atoms in each molecule will be shifted towards the molecule
            centre. If False, they will be shifted to the first atom. By default False

        Returns
        -------
        PeriodicFractionalConfiguration
            A configuration instance containing shifted atom positions.
        """

        contiguous_coords = contiguous_coordinates_fractional(
            self._variables["coordinates"],
            indices_grouped,
            bring_to_centre,
        )

        conf = self.clone()
        conf._variables["coordinates"] = contiguous_coords
        return conf


class PeriodicAbsoluteConfiguration(_PeriodicConfiguration):
    is_periodic = True

    def to_fractional_coordinates(self) -> FloatArray:
        """Return atom positions as fractional coordinates in the current unit cell."""
        return np.matmul(self._variables["coordinates"], self._unit_cell.inverse)

    def to_fractional_configuration(self) -> PeriodicFractionalConfiguration:
        """Return atom fractional coordinates in a configuration instance."""

        coords = self.to_fractional_coordinates()

        variables = copy.deepcopy(self._variables)
        variables.pop("coordinates")

        box_conf = PeriodicFractionalConfiguration(coords, self._unit_cell, **variables)

        return box_conf

    def to_absolute_coordinates(self) -> FloatArray:
        """Return atom positions as an array of absolute coordinates."""
        return self._variables["coordinates"]

    def contiguous_configuration(
        self, indices_grouped: Sequence[Sequence[int]], bring_to_centre: bool = False
    ) -> PeriodicAbsoluteConfiguration:
        """Return atoms positions made contiguous in a configuration instance.

        Normally, for each index list in the input, atoms are translated by
        unit cell vectors to be as close as possible to the first atom in the list.

        Parameters
        ----------
        indices_grouped : Sequence[Sequence[int]]
            A list of atom coordinate lists, one per molecule.
        bring_to_centre : bool, optional
            Shift atoms closer to the molecule centre, by default False

        Returns
        -------
        PeriodicAbsoluteConfiguration
            Configuration instance containing the shifted coordinates.
        """

        contiguous_coords = contiguous_coordinates_absolute(
            self._variables["coordinates"],
            self._unit_cell.direct,
            self._unit_cell.inverse,
            indices_grouped,
            bring_to_centre,
        )

        conf = self.clone()
        conf._variables["coordinates"] = contiguous_coords
        return conf

    def continuous_configuration(
        self, bonds: Sequence[Sequence[int]]
    ) -> PeriodicAbsoluteConfiguration:
        """Return atom positions in a configuration with continuous molecules.

        The continuous coordinates are made by translating atoms by unit cell vectors
        to ensure that none of the bonds in the input list are broken. This may not
        work for large molecules, and is certain not to work correctly for infinite
        molecular chains.

        Parameters
        ----------
        bonds : Sequence[Sequence[int]]
            List of pairs of atom indices defining chemical bonds in the system.

        Returns
        -------
        PeriodicAbsoluteConfiguration
            Configuration instance containing shifted atoms with continuous molecules.
        """

        continuous_coords = continuous_coordinates(
            self._variables["coordinates"],
            self._unit_cell.direct,
            self._unit_cell.inverse,
            bonds,
        )

        conf = self.clone()
        conf._variables["coordinates"] = continuous_coords
        return conf


class AbsoluteConfiguration(_Configuration):
    is_periodic = False

    def clone(self) -> AbsoluteConfiguration:
        """Return a copy of itself."""

        variables = copy.deepcopy(self.variables)

        coords = variables.pop("coordinates")

        return self.__class__(coords, **variables)

    def fold_coordinates(self) -> None:
        """Do nothing. Folding is not possible without a unit cell."""
        return

    def to_absolute_coordinates(self) -> FloatArray:
        """Return the atom coordinates."""
        return self._variables["coordinates"]

    def contiguous_configuration(
        self, _: Any = None, bring_to_centre: bool = False
    ) -> AbsoluteConfiguration:
        """Return itself. A dummy operation, included for compatibility.

        Parameters
        ----------
        _ : Any, optional
            Ignored, by default None
        bring_to_centre : bool, optional
            Ignored, by default False

        Returns
        -------
        AbsoluteConfiguration
            This configuration instance.
        """
        return self

    def continuous_configuration(self, _: Any = None) -> AbsoluteConfiguration:
        """Return itself. Included for compatibility with other configurations.

        Parameters
        ----------
        _ : Any, optional
            Ignored, by default None

        Returns
        -------
        AbsoluteConfiguration
            This configuration instance.
        """
        return self
