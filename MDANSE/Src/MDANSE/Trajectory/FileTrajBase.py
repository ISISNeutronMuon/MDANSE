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

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path

import h5py
import numpy as np
import numpy.typing as npt

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import (
    _Configuration,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import atomic_trajectory
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class TrajectoryFile(ABC):
    """Abstract base class for objects which implement trajectories."""

    def __contains__(self, key: str) -> bool:
        return self.has_variable(key)

    def __getstate__(self) -> dict:
        d = self.__dict__.copy()
        del d["_h5_file"]
        return d

    def __setstate__(self, state: dict) -> None:
        self.__dict__ = state
        self._h5_file = h5py.File(state["_h5_filename"], "r")

    def _check_frame(self, frame: slice | int) -> None:
        """Check frame in bounds.

        Parameters
        ----------
        frame : slice or int
            User selected frame.

        Raises
        ------
        IndexError
            If frame outside valid region.
        """
        if isinstance(frame, int) and 0 > frame >= len(self):
            raise IndexError(
                f"Invalid frame number ({frame}) outside bounds (0, {len(self)})."
            )
        elif isinstance(frame, slice):
            start, stop, _ = frame.indices(len(self))
            if 0 > start >= len(self):
                raise IndexError(
                    f"Invalid frame slice start ({frame}) outside bounds (0, {len(self)})."
                )
            if 0 > stop >= len(self):
                raise IndexError(
                    f"Invalid frame slice stop ({frame}) outside bounds (0, {len(self)})."
                )

    @classmethod
    @abstractmethod
    def file_is_right(self, filename: Path | str) -> bool: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def __getitem__(self, frame: int) -> dict[str, npt.NDArray[float]]: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def charges(
        self,
        frame: int,
        indices: slice | int = np.s_[:],
    ) -> npt.NDArray[float]: ...

    @abstractmethod
    def coordinates(
        self, frame: slice | int, indices: slice | int = np.s_[:]
    ) -> npt.NDArray[float]: ...

    @abstractmethod
    def configuration(self, frame: int = 0) -> _Configuration: ...

    @abstractmethod
    def time(self) -> npt.NDArray[float]: ...

    @abstractmethod
    def unit_cell(self, frame: int) -> UnitCell | None: ...

    @abstractmethod
    def masses(self) -> npt.NDArray[float]: ...

    @abstractmethod
    def variables(self) -> list[str]: ...

    @abstractmethod
    def variable(self, name: str) -> npt.ArrayLike: ...

    @abstractmethod
    def has_variable(self, variable: str) -> bool: ...

    @abstractmethod
    def get_atom_property(
        self, atom_symbol: str, atom_property: str
    ) -> int | float | complex | str: ...

    @property
    def units(self) -> Mapping[str, str]:
        """Mapping of property labels to units."""
        return ATOMS_DATABASE.units

    def read_configuration_trajectory(
        self,
        index: int,
        first: int = 0,
        last: int | None = None,
        step: int = 1,
        variable: str = "velocities",
    ) -> npt.NDArray[float]:
        """Return trajectory values for one atom for a subset of frames.

        Parameters
        ----------
        index : int
            Atom index.
        first : int, optional
            First frame index, by default 0
        last : int | None, optional
            Last frame index, by default None
        step : int, optional
            Step in time frames, by default 1
        variable : str, optional
            Value to be read from trajectory, by default "velocities"

        Returns
        -------
        ndarray
            Value of 'variable' for one atom and selected frames.

        Raises
        ------
        KeyError
            If 'variable' is not in the trajectory file.

        """
        slc = np.s_[first:last:step]
        self._check_frame(slc)

        if not self.has_variable(variable):
            raise KeyError(
                f"The variable {variable} is not stored in trajectory {self._h5_filename}"
            )

        return self.variable(variable)[slc, index, :].astype(np.float64)

    def to_real_coordinates(
        self,
        box_coordinates: npt.NDArray[float],
        first: int = 0,
        last: int | None = None,
        step: int | None = None,
    ) -> npt.NDArray[float]:
        """Convert box coordinates to real coordinates for a set of frames.

        Parameters
        ----------
        box_coordinates : ndarray
            A 2D array containing the box coordinates.
        first : int
            The index of the first frame.
        last : int or None
            The index of the last frame.
        step : int or None
            The step in frame.

        Returns
        -------
        ndarray
            2D array containing the real coordinates converted from box coordinates.

        """
        if self._unit_cells is not None:
            real_coordinates = np.empty_like(box_coordinates)

            for comp, cell in enumerate(self._unit_cells[first:last:step]):
                real_coordinates[comp, :] = box_coordinates[comp, :] @ cell.direct
            return real_coordinates

        return box_coordinates

    def read_atomic_trajectory(
        self,
        index: int,
        first: int = 0,
        last: int | None = None,
        step: int | None = 1,
        *,
        box_coordinates: bool = False,
    ) -> npt.NDArray[float]:
        """Read an atomic trajectory. The trajectory is corrected from box jumps.

        Parameters
        ----------
        index : int
            The index of the atom.
        first : int
            The index of the first frame. (Default value = 0)
        last : int
            The index of the last frame. (Default value = None)
        step : int
            The step in frame. (Default value = 1)
        box_coordinates : bool
            If True, the coordiniates are returned in box coordinates (Default value = False).

        Returns
        -------
        ndarray
            2D array containing the atomic trajectory for the selected frames

        """
        slc = np.s_[first:last:step]

        coords = self.coordinates(slc, index)

        if self._unit_cells is None:
            return coords

        direct_cells = np.array([cell.direct for cell in self._unit_cells[slc]])
        inverse_cells = np.array([cell.inverse for cell in self._unit_cells[slc]])
        return atomic_trajectory(
            coords,
            direct_cells,
            inverse_cells,
            box_coordinates=box_coordinates,
        )

    @property
    def chemical_system(self) -> ChemicalSystem:
        """Return the ChemicalSystem of this trajectory.

        Returns
        -------
        ChemicalSystem
            Object storing the information about atoms and bonds

        """
        return self._chemical_system

    @property
    def file(self) -> h5py.File:
        """Return the trajectory file object.

        Returns
        -------
        h5py.File
            The trajectory file object.

        """
        return self._h5_file

    @property
    def filename(self) -> str:
        """Return the trajectory filename.

        Returns
        -------
        str
            The trajectory filename.

        """
        return str(self._h5_filename)
