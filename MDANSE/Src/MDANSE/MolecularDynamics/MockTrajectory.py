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

import json
import math
from typing import TypeVar

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
    _Configuration,
    contiguous_coordinates_real,
)
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.MolecularDynamics.TrajectoryUtils import atomic_trajectory
from MDANSE.MolecularDynamics.UnitCell import UnitCell

Self = TypeVar("Self", bound="MockTrajectory")


class MockTrajectory:
    """For testing purposes, MockTrajectory can replace a trajectory.
    It acts as a trajectory of predefined composition and size,
    while taking only a necessary minimum of resources.
    The main goal is performance testing of different analysis types
    without the need to run Molecular Dynamics simulations beforehand.
    """

    def __init__(
        self,
        number_of_frames: int = 1000,
        atoms_in_box: tuple = ("Si",),
        time_step: float = 1.0,
        box_repetitions: tuple = (2, 3, 1),
        box_size: np.ndarray = 10.0 * np.eye(3),
        pbc: bool = False,
    ):
        self._number_of_frames = number_of_frames
        self._box_repetitions = box_repetitions
        multiplier = box_repetitions[0] * box_repetitions[1] * box_repetitions[2]
        self._atom_types = list(atoms_in_box) * multiplier
        self._multiplier = multiplier
        self._pbc = pbc
        self._time_step = time_step * measure(1.0, "fs").toval("ps")
        self._time_axis = np.arange(
            0.0, number_of_frames * self._time_step, self._time_step
        )
        self._box_size = box_size * measure(1.0, "ang").toval("nm")
        self._real_length = 0
        self._num_atoms_in_box = len(atoms_in_box)
        self._full_box_size = np.vstack(
            [
                box_repetitions[0] * self._box_size[0, :],
                box_repetitions[1] * self._box_size[1, :],
                box_repetitions[2] * self._box_size[2, :],
            ]
        )
        self._variables = {}
        self._coordinates = None

        self._chemical_system = ChemicalSystem("MockSystem")
        self._chemical_system.initialise_atoms(self._atom_types)

    def set_coordinates(self, coords: np.ndarray):
        """Sets the initial (equlibrium) positions of atoms from
        the input array.

        The array must have as many rows as there are atoms in a single box,
        and the positions will be replicated between boxes.

        Parameters
        ----------
        coords : np.ndarray
            positions of atoms in a single box

        Returns
        -------
        bool
            False if the number of elements was wrong
        """
        if len(coords) != self._num_atoms_in_box:
            return False
        coords_nm = coords * measure(1.0, "ang").toval("nm")
        copies = []
        A, B, C = self._box_repetitions
        vA, vB, vC = self._box_size[0, :], self._box_size[1, :], self._box_size[2, :]
        for na in range(A):
            for nb in range(B):
                for nc in range(C):
                    shift = na * vA + nb * vB + nc * vC
                    copies.append(coords_nm + shift.reshape((1, 3)))
        self._start_coordinates = np.vstack(copies)

    def modulate_structure(
        self,
        polarisation: np.ndarray,
        propagation_vector: np.ndarray,
        period: int = 10,
        amplitude: float = 0.1,
    ):
        """Creates a number of frames in the trajectory which contain
        coordinates displaced by a mechanical wave. The atom positions
        oscillate around the equlibrium positions.

        Parameters
        ----------
        polarisation : np.ndarray
            direction of atom displacements
        propagation_vector : np.ndarray
            propagation vector of the wave (phonon). All zeros for standing wave
        period : int, optional
            Number of frames corresponding to a total 2pi period of the wave.
        amplitude : float, optional
            Maximum displacement along the polarisation vector (in Angstrom)

        Returns
        -------
        bool
            False on wrong size of the input array

        Raises
        ------
        ValueError
            if the period of the new modulation is incommensurate with the number of frames
        """
        if len(polarisation) * self._multiplier == len(self._start_coordinates):
            polarisation = np.vstack(self._multiplier * [polarisation])
        if len(polarisation) != len(self._start_coordinates):
            return False
        n_steps = period
        n_atoms = len(self._start_coordinates)
        if self._coordinates is None:
            self._coordinates = np.empty((period, n_atoms, 3))
        else:
            current_steps = len(self._coordinates)
            if current_steps % period:
                raise ValueError(
                    f"Incommensurate vibration frequencies are not supported.\n"
                    f"Trajectory length: {self._number_of_frames}, current_steps: {current_steps}, modulation period: {period}"
                )
            if current_steps > period:
                n_steps = current_steps
            if current_steps < period:
                step = math.gcd(current_steps, period)
                while len(self._coordinates) < period:
                    self._coordinates = np.vstack(
                        [self._coordinates, self._coordinates[-step:]]
                    )
        nm_amp = amplitude * measure(1.0, "ang").toval("nm")
        unit_cell = UnitCell(self._full_box_size)
        inverse_cell = unit_cell._inverse_unit_cell
        shift = np.array(polarisation) * nm_amp
        k_vector = np.array(
            [
                propagation_vector[0] * inverse_cell[0],
                propagation_vector[1] * inverse_cell[1],
                propagation_vector[2] * inverse_cell[2],
            ]
        ).sum(axis=0)
        # phase should be an array of the dimensions:
        # (n_time_steps=period, n_atoms)
        time_part = (np.arange(period) / period).reshape((period, 1))
        space_part = np.dot(k_vector, self._start_coordinates.T).reshape((1, n_atoms))
        phase = np.sin(2 * np.pi * (time_part + space_part))
        # now we generate the offsets
        for n in range(n_steps):
            self._coordinates[n] = self.coordinates(n) + phase[n % period].reshape(
                (n_atoms, 1)
            ) * shift.reshape((n_atoms, 3))
        self._real_length = n_steps

    def close(self):
        """Present for compatibility with Trajectory"""

    def __getitem__(self, frame: int):
        """Returns the configuration of the system at the Nth frame.

        Parameters
        ----------
        frame : int
            number of the frame at which to get the configuration

        Returns
        -------
        dict
            coordinates, time and unit cell at the specified frame

        Raises
        ------
        IndexError
            if frame is outside of range
        """
        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        configuration = {}
        configuration["coordinates"] = self.coordinates(frame).astype(np.float64)
        configuration["time"] = self._time_axis[frame]
        configuration["unit_cell"] = self.unit_cell(frame)._unit_cell.astype(np.float64)

        return configuration

    def __getstate__(self):
        """Only added for compatibility with Trajectory"""
        pass

    def __setstate__(self, state):
        """Only added for compatibility with Trajectory"""
        pass

    def time(self) -> np.ndarray:
        return self._time_axis

    def coordinates(
        self, frame: int, atom_indices: slice | int = slice(None)
    ) -> np.ndarray:
        """Returns the atom coordinates at the specified frame

        Parameters
        ----------
        frame : int
            number of the simulation step (frame)

        Returns
        -------
        np.ndarray
            an array (N,3) of atom coordinates. N is the numer of atoms.

        Raises
        ------
        IndexError
            if frame is out of range
        """

        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        if self._real_length < 1:
            return self._start_coordinates.astype(np.float64)

        scaled_index = frame % self._real_length

        return self._coordinates[scaled_index, atom_indices, :].astype(np.float64)

    def configuration(self, frame: int) -> _Configuration:
        """An MDANSE Configuration at the specified frame number.

        Parameters
        ----------
        frame : int
            number of the simulation step (frame)

        Returns
        -------
        _Configuration
            An object holding the atom positions, unit cell, etc.

        Raises
        ------
        IndexError
            if frame is out of range
        """

        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        unit_cell = UnitCell(self._full_box_size)

        variables = {}

        coordinates = self.coordinates(frame)

        if self._pbc:
            conf = PeriodicRealConfiguration(
                self._chemical_system, coordinates, unit_cell, **variables
            )
        else:
            conf = RealConfiguration(self._chemical_system, coordinates, **variables)

        return conf

    def _load_unit_cells(self):
        """Only added for compatibility with Trajectory."""

    def get_atom_property(self, atom_symbol: str, atom_property: str):
        return ATOMS_DATABASE.get_atom_property(atom_symbol, atom_property)

    def atoms(self) -> list[str]:
        return ATOMS_DATABASE.atoms

    def properties(self) -> list[str]:
        return ATOMS_DATABASE.properties

    def unit_cell(self, frame: int) -> UnitCell:
        """Returns the UnitCell the size of the system.

        Parameters
        ----------
        frame : int
            ignored

        Returns
        -------
        UnitCell
            Object defining the system size
        """

        return UnitCell(self._full_box_size)

    def __len__(self) -> int:
        """Length of the mock trajectory

        Returns
        -------
        int
            number of frames that can be returned by MockTrajectory
        """

        return self._number_of_frames

    def read_com_trajectory(
        self, indices, first=0, last=None, step=1, box_coordinates=False
    ):
        """Build the trajectory of the center of mass of a set of atoms.

        :param atoms: the atoms for which the center of mass should be computed
        :type atoms: list MDANSE.Chemistry.ChemicalSystem.Atom
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

        masses = np.array(
            [
                self.chemical_system.atom_property("atomic_weight")[index]
                for index in indices
            ]
        )

        frames = np.array([self.coordinates(fnum) for fnum in range(first, last, step)])
        coords = frames[:, indices, :].astype(np.float64)

        if coords.ndim == 2:
            coords = coords[np.newaxis, :, :]

        if self._pbc:
            direct_cells = np.array(
                [self.unit_cell(fnum).direct for fnum in range(first, last, step)]
            )
            inverse_cells = np.array(
                [self.unit_cell(fnum).inverse for fnum in range(first, last, step)]
            )
            temp_coords = contiguous_coordinates_real(
                coords,
                direct_cells,
                inverse_cells,
                [list(range(len(coords)))],
                bring_to_centre=True,
            )
            com_coords = np.vstack(
                [
                    center_of_mass(temp_coords[tstep], masses)
                    for tstep in range(len(temp_coords))
                ]
            )

            com_traj = atomic_trajectory(com_coords, direct_cells, inverse_cells)

        else:
            com_traj = np.sum(
                coords[:, indices, :] * masses[np.newaxis, :, np.newaxis], axis=1
            )
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

        if self._pbc:
            real_coordinates = np.empty(box_coordinates.shape, dtype=np.float64)
            for comp, i in enumerate(range(first, last, step)):
                direct_cell = self.unit_cell(i).direct
                real_coordinates[comp, :] = box_coordinates[comp, :] @ direct_cell
            return real_coordinates
        else:
            return box_coordinates

    def read_atomic_trajectory(
        self,
        index: int,
        first: int = 0,
        last: int | None = None,
        step: int = 1,
        *,
        box_coordinates: bool = False,
    ):
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

        frames = np.array([self.coordinates(fnum) for fnum in range(first, last, step)])
        coords = frames[:, index, :].astype(np.float64)

        if self._pbc:
            direct_cells = np.array(
                [self.unit_cell(fnum).direct for fnum in range(first, last, step)]
            )
            inverse_cells = np.array(
                [self.unit_cell(fnum).inverse for fnum in range(first, last, step)]
            )
            atomic_traj = atomic_trajectory(
                coords, direct_cells, inverse_cells, box_coordinates=box_coordinates
            )
            return atomic_traj
        else:
            return coords

    def read_configuration_trajectory(
        self, index, first=0, last=None, step=1, variable="velocities"
    ):
        """Read a given configuration variable through the trajectory for a given ato.

        :param index: the index of the atom
        :type index: int
        :param first: the index of the first frame
        :type first: int
        :param last: the index of the last frame
        :type last: int
        :param step: the step in frame
        :type step: int
        :param variable: the configuration variable to read
        :type variable: str

        :return: 2D array containing the atomic trajectory for the selected frames
        :rtype: ndarray
        """

        if last is None:
            last = len(self)

        grp = self._variables

        if variable not in grp:
            raise KeyError(f"The variable {variable} is not stored in the trajectory")

        variable = grp[variable][first:last:step, index, :].astype(np.float64)

        return variable

    @property
    def chemical_system(self):
        """Return the chemical system stored in the trajectory.

        :return: the chemical system
        :rtype: MDANSE.Chemistry.ChemicalSystem.ChemicalSystem
        """
        return self._chemical_system

    @property
    def file(self) -> str:
        """There is no trajectory file.
        A string is returned instead.

        :return: the trajectory file object
        :rtype: HDF5 file object
        """

        return "nonexistent_file.h5"

    @property
    def filename(self) -> str:
        """Returns a file name, but the file does not exist.

        :return: the trajectory filename
        :rtype: str
        """

        return "nonexistent_file.h5"

    @property
    def has_velocities(self) -> bool:
        """True if the trajectory contains atom velocities,
        False otherwise.

        Returns
        -------
        bool
            True if velocities are stored in MockTrajectory
        """
        return "velocities" in self._variables.keys()

    def has_variable(self, variable: str) -> bool:
        """True if the trajectory contains atom velocities,
        False otherwise.

        Returns
        -------
        bool
            True if velocities are stored in MockTrajectory
        """
        return variable in self._variables.keys()

    def variables(self):
        """Return the configuration variables stored in this trajectory.
        Most likely empty for MockTrajectory, but does not have to be.

        :return; the configuration variable
        :rtype: list
        """

        grp = self._variables

        return list(grp.keys())

    @classmethod
    def from_json(cls, filename: str) -> Trajectory:
        """Builds and returns an instance of MockTrajectory
        using the parameters in a JSON file.

        Parameters
        ----------
        filename : str
            must be a valid JSON file with "parameters",
            "coordinates" and "modulations" sections.

        Returns
        -------
        Trajectory
            a Trajectory instance with a MockTrajectory as internal object
        """
        with open(filename, encoding="utf-8") as source:
            struct = json.load(source)
        temp = struct["parameters"]
        temp["box_size"] = np.array(temp["box_size"])
        instance = cls(**temp)
        instance.set_coordinates(np.array(struct["coordinates"]))
        for pdict in struct["modulations"]:
            temp = pdict
            temp["polarisation"] = np.array(temp["polarisation"])
            temp["propagation_vector"] = np.array(temp["propagation_vector"])
            instance.modulate_structure(**temp)
        wrapper = Trajectory(None, trajectory_format="mock")
        wrapper._trajectory = instance
        return wrapper
