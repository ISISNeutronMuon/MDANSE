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
from enum import Enum, auto
from typing import TYPE_CHECKING

import h5py
import numpy as np
import numpy.typing as npt

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.TrajectoryUtils import (
    atomic_trajectory,
    atomic_trajectory_many,
)
from MDANSE.MolecularDynamics.UnitCell import (
    BAD_CELL,
    CELL_SIZE_LIMIT,
    CHANGING_CELL,
    NO_CELL,
    UnitCell,
)
from MDANSE.util_types import FloatArray

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
    from MDANSE.MolecularDynamics.Configuration import (
        _Configuration,
    )


class TrajDataArray(Enum):
    POSITION = auto()
    VELOCITY = auto()
    FORCE = auto()
    POSITIONS = POSITION
    VELOCITIES = VELOCITY
    FORCES = FORCE
    GRADIENTS = FORCE
    GRADIENT = FORCE


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
        self._h5_file = h5py.File(
            state["_h5_filename"],
            "r",
            driver=state["_h5_driver"],
            rdcc_nbytes=state["_h5_cache_size"],
        )

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
    def __getitem__(self, frame: int) -> dict[str, FloatArray]: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def charges(
        self,
        frame: int,
        indices: slice | int = np.s_[:],
    ) -> FloatArray: ...

    @abstractmethod
    def coordinates(
        self, frame: slice | int, indices: slice | int = np.s_[:]
    ) -> FloatArray: ...

    @abstractmethod
    def configuration(self, frame: int = 0) -> _Configuration: ...

    @abstractmethod
    def time(self) -> FloatArray: ...

    def chunk_size(self, dataset_type: TrajDataArray = TrajDataArray.POSITION) -> int:
        data_key = self.KEYS[dataset_type.name.lower()]
        try:
            dataset = self._h5_file[data_key]
        except KeyError:
            LOG.error("Dataset %s was not in the trajectory file", data_key)
            return -1
        if (chunk_shape := getattr(dataset, "chunks", None)) is None:
            LOG.warning("Dataset %s is not chunked, and was expected to be", data_key)
            return -1
        if len(chunk_shape) < 2:
            LOG.warning("Dataset %s does not have enough dimensions", data_key)
            return -1
        return chunk_shape[1]

    def dtype_size(self, dataset_type: TrajDataArray = TrajDataArray.POSITION) -> int:
        data_key = self.KEYS[dataset_type.name.lower()]
        dataset = self._h5_file[data_key]
        match dataset.dtype:
            case np.float16:
                return 2
            case np.float32:
                return 4
            case np.float64:
                return 8
            case np.float128:
                return 16
            case _:
                return 8

    def unit_cell(self, frame: int) -> UnitCell | None:
        """Return the unit cell at a given frame.

        Parameters
        ----------
        frame : int
            Index of the selected trajectory frame.

        Returns
        -------
        UnitCell | None
            Unit cell definition. None if no cell is defined in the trajectory.

        Raises
        ------
        IndexError
            If frame index is out of the range covered by the trajectory.

        """
        if self.unit_cell_warning == NO_CELL:
            return None
        self._check_frame(frame)
        return UnitCell(self.unit_cells_raw[frame].astype(np.float64))

    def check_unit_cells(self):
        """Checks the unit cells and updates the warning."""
        self.unit_cell_warning = ""

        if self.unit_cells_raw is None:
            self.unit_cell_warning = NO_CELL
            return

        if not self.unit_cell_warning:
            if self.unit_cell(0).volume < CELL_SIZE_LIMIT:
                self.unit_cell_warning = BAD_CELL
                return

            reference_array = self.unit_cells_raw[0]

            if self.unit_cells_raw.shape[0] > 1:
                directs = self.unit_cells_raw[1:]
                if not np.allclose(directs, reference_array):
                    self.unit_cell_warning = CHANGING_CELL
                    return

    @abstractmethod
    def masses(self) -> FloatArray: ...

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
        slc: slice | None = None,
        variable: str = "velocities",
    ) -> FloatArray:
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
        slc : slice | None, default None
            Slice of time frames to be used, optional.
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
        if slc is None:
            slc = np.s_[first:last:step]
            self._check_frame(slc)

        if not self.has_variable(variable):
            raise KeyError(
                f"The variable {variable} is not stored in trajectory {self._h5_filename}"
            )

        return self.variable(variable)[slc, index, :].astype(np.float64)

    def to_absolute_coordinates(
        self,
        fractional_coordinates: FloatArray,
        first: int = 0,
        last: int | None = None,
        step: int | None = None,
    ) -> FloatArray:
        """Convert fractional coordinates to absolute coordinates for a set of frames.

        Parameters
        ----------
        fractional_coordinates : ndarray
            A 2D array containing the fractional coordinates.
        first : int
            The index of the first frame.
        last : int or None
            The index of the last frame.
        step : int or None
            The step in frame.

        Returns
        -------
        ndarray
            2D array containing the absolute coordinates converted from fractional coordinates.

        """
        if self.unit_cell_warning == NO_CELL:
            return fractional_coordinates
        return fractional_coordinates @ self.unit_cells_raw[first:last:step]

    def read_atomic_trajectory_many(
        self,
        index_list: list[int],
        first: int = 0,
        last: int | None = None,
        step: int = 1,
        *,
        fractional_coordinates: bool = False,
        reference: FloatArray | None = None,
    ) -> FloatArray:
        """Read continuous trajectories of multiple atoms.

        Parameters
        ----------
        index : list[int]
            Indices of atoms to be read.
        first : int, default 0
            The index of the first frame.
        last : int | None, default None
            The index of the last frame.
        step : int, default 1
            The step in frame.
        fractional_coordinates : bool, default False.
            If True, the coordinates are returned in fractional coordinates.

        Returns
        -------
        ndarray
            (N_FRAMES, N_ATOMS, 3) array of coordinates.

        """
        slc = np.s_[first:last:step]

        coords = self.coordinates(slc, index_list)

        if self.unit_cell_warning == NO_CELL:
            return coords

        direct_cells = self.unit_cells_raw[slc]
        inverse_cells = np.linalg.pinv(direct_cells)
        return atomic_trajectory_many(
            coords,
            direct_cells,
            inverse_cells,
            fractional_coordinates=fractional_coordinates,
            reference=reference,
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
