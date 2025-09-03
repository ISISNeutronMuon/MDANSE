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

from collections.abc import Iterable
from enum import Enum
from pathlib import Path

import h5py
import numpy as np
import numpy.typing as npt

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
    _Configuration,
    contiguous_coordinates_real,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import (
    atomic_trajectory,
)
from MDANSE.MolecularDynamics.UnitCell import (
    BAD_CELL,
    CELL_SIZE_LIMIT,
    CHANGING_CELL,
    NO_CELL,
    UnitCell,
)

from .FileTrajBase import TrajectoryFile

SLICE_ALL = np.s_[:]


class H5MDTrajectory(TrajectoryFile):
    """This is used by Trajectory, which is now a wrapper object.

    The H5MDTrajectory for now has been prepared to read the
    H5MD files created by MDMC.
    """

    UNIT_MAP = {
        "Ang": "ang",
        "Angstrom": "ang",
    }

    UNIT_CONV = {
        "position": "nm",
        "box": "nm",
        "velocity": "nm/ps",
        "time": "ps",
    }

    KEYS = {
        "position": "/particles/all/position/value",
        "velocity": "/particles/all/velocity/value",
        "box": "/particles/all/box/edges/value",
        "time": "/particles/all/position/time",
    }

    class MassLoc(Enum):
        """Mass location in H5MD."""

        PER_STEP = "/particles/all/mass/value"
        GLOBAL = "/particles/all/mass"
        NONE = None

    class ChargeLoc(Enum):
        """Charge location in H5MD."""

        PER_STEP = "/particles/all/charge/value"
        GLOBAL = "/particles/all/charge"
        NONE = None

    @property
    def pos_key(self) -> str:
        return self.KEYS["position"]

    @property
    def vel_key(self) -> str:
        return self.KEYS["velocity"]

    @property
    def box_key(self) -> str:
        return self.KEYS["box"]

    @property
    def time_key(self) -> str:
        return self.KEYS["time"]

    @property
    def charge_key(self) -> str:
        for loc in (self.ChargeLoc.PER_STEP, self.ChargeLoc.GLOBAL):
            if loc.value in self._h5_file:
                return loc

        return self.ChargeLoc.NONE

    @property
    def mass_key(self) -> str:
        for loc in (self.MassLoc.PER_STEP, self.MassLoc.GLOBAL):
            if loc.value in self._h5_file:
                return loc

        return self.MassLoc.NONE

    @property
    def positions(self) -> h5py.Dataset:
        return self._h5_file[self.pos_key]

    @property
    def velocities(self) -> h5py.Dataset:
        return self._h5_file[self.vel_key]

    def __init__(self, h5_filename: Path | str):
        """Constructor.

        Parameters
        ----------
        h5_filename : Path or str
            The trajectory filename.
        """
        self.unit_cell_warning = ""

        self._h5_filename = Path(h5_filename)

        self._h5_file = h5py.File(self._h5_filename, "r")
        particle_types = self._h5_file["/particles/all/species"]
        particle_lookup = h5py.check_enum_dtype(
            self._h5_file["/particles/all/species"].dtype
        )

        if particle_lookup is None:
            # Load the chemical system
            try:
                symbols = self._h5_file["/parameters/atom_symbols"]
            except KeyError:
                LOG.error(
                    f"No information about chemical elements in {self._h5_filename}"
                )
                return

            chemical_elements = [byte.decode() for byte in symbols]
        else:
            reverse_lookup = {item: key for key, item in particle_lookup.items()}
            chemical_elements = [
                reverse_lookup[type_number] for type_number in particle_types
            ]
        self._chemical_system = ChemicalSystem(self._h5_filename.stem)

        try:
            self._chemical_system.initialise_atoms(chemical_elements)
        except (KeyError, TypeError):
            LOG.error(
                "It was not possible to read chemical element information from an H5MD file."
            )
            return

        self._variables_to_skip = set()
        self._load_units()

        self._load_unit_cells()

    def _load_units(self) -> None:
        """Load units from h5 file."""
        self.units = {}

        for name, loc in self.KEYS.items():
            if loc not in self._h5_file:
                LOG.info("No %s block in input.", name)
                continue

            if "unit" in (d := self._h5_file[loc].attrs):
                unit = d["unit"]
                for orig, rep in self.UNIT_MAP.items():
                    unit = unit.replace(orig, rep)
                self.units[name] = measure(1.0, unit).toval(self.UNIT_CONV[name])
            else:
                LOG.warning("No units for %s, using default of 1.0.", name)
                self.units[name] = 1.0

    @classmethod
    def file_is_right(self, filename: Path | str) -> bool:
        """Check if the input file is likely to be an H5MD trajectory.

        Parameters
        ----------
        filename : Path | str
            File to check.

        Returns
        -------
        bool
            Whether file should be loaded as H5MD.

        """
        try:
            with h5py.File(filename) as temp:
                temp["h5md"]
        except Exception:
            return False

        return True

    def close(self):
        """Close the trajectory."""

        self._h5_file.close()

    def __getitem__(self, frame: int) -> dict[str, npt.NDArray[float]]:
        """Return the configuration at a given frame.

        Parameters
        ----------
        frame : int
            Frame to get.

        Returns
        -------
        dict[str, npt.NDArray[float]]
            Configuration at frame.
        """
        self._check_frame(frame)

        grp = self.positions

        configuration = {
            "coordinates": grp[frame, :, :] * self.units["position"],
            "time": self.time()[frame],
        }

        if self.vel_key in self._h5_file:
            configuration["velocities"] = (
                self.velocities[frame, :, :] * self.units["velocity"]
            )

        if self._unit_cells is not None:
            try:
                configuration["unit_cell"] = self._unit_cells[frame]
            except IndexError:
                configuration["unit_cell"] = self._unit_cells[0]

        return configuration

    def charges(self, frame: int) -> npt.NDArray[float]:
        """Return the electrical charge of atoms at a given frame.

        Parameters
        ----------
        frame : int
            Frame to load.

        Returns
        -------
        ndarray
            Charges at given time.

        """
        if 0 > frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        key = self.charge_key
        if key is self.ChargeLoc.PER_STEP:
            charge = self._h5_file[key.value][frame]
        elif key is self.ChargeLoc.GLOBAL:
            charge = self._h5_file[key.value][:]
        elif key is self.ChargeLoc.NONE:
            LOG.debug(f"No charge information in trajectory {self._h5_filename}")
            charge = np.zeros(self._chemical_system.number_of_atoms)

        return charge.astype(np.float64)

    def coordinates(
        self,
        frame: slice | int,
        atom_indices: slice | int = SLICE_ALL,
    ) -> npt.NDArray[float]:
        """Return the coordinates at a given frame.

        Parameters
        ----------
        frame : slice or int
            Frame(s) to load.
        atom_indices : slice or int
            Atoms to select.

        Returns
        -------
        ndarray
            The coordinates in given frame.

        """
        self._check_frame(frame)

        retval = self.positions[frame, atom_indices, :]

        return retval.astype(np.float64) * self.units["position"]

    def configuration(self, frame: int = 0) -> _Configuration:
        """Build and return a configuration at a given frame.

        Parameters
        ----------
        frame : int
            Frame to load.

        Returns
        -------
        _Configuration
            The configuration.

        """
        self._check_frame(frame)

        unit_cell = self.unit_cell(frame) if self._unit_cells is not None else None

        variables = {}
        for k in self.variables():
            if k not in self._variables_to_skip:
                try:
                    variables[k] = self.variable(k)[frame, :, :].astype(np.float64)
                except Exception:
                    self._variables_to_skip.add(k)

        coordinates = self.coordinates(frame)

        if unit_cell is None:
            conf = RealConfiguration(self._chemical_system, coordinates, **variables)
        else:
            conf = PeriodicRealConfiguration(
                self._chemical_system, coordinates, unit_cell, **variables
            )

        return conf

    def _load_unit_cells(self) -> None:
        """Load all the unit cells."""
        self._unit_cells = []

        try:
            cells = self._h5_file[self.box_key][:] * self.units["box"]
        except KeyError:
            self._unit_cells = None
            self.unit_cell_warning = NO_CELL
            return

        if cells.ndim > 1:
            for cell in cells:
                if cell.shape == (3, 3):
                    temp_array = np.array(cell)
                elif cell.shape == (3,):
                    temp_array = np.diag(cell)
                else:
                    raise ValueError(
                        f"Cell array {cell} has a wrong shape {cell.shape}"
                    )
                uc = UnitCell(temp_array)
                self._unit_cells.append(uc)
                if not self.unit_cell_warning and uc.volume < CELL_SIZE_LIMIT:
                    self.unit_cell_warning = BAD_CELL
        else:
            temp_array = np.diag(cells)
            self._unit_cells.append(UnitCell(temp_array))

        if not self.unit_cell_warning:
            reference_array = self._unit_cells[0].direct
            for uc in self._unit_cells[1:]:
                if not np.allclose(reference_array, uc.direct):
                    self.unit_cell_warning = CHANGING_CELL
                    return

    def time(self) -> npt.NDArray[float]:
        """Time timesteps from file."""

        try:
            time = self._h5_file[self.time_key][:] * self.units["time"]
        except Exception:
            LOG.warning("Time may be invalid in H5MD file.")
            time = np.array([], dtype=np.float64)

        return time

    def unit_cell(self, frame: int) -> UnitCell | None:
        """Return the unit cell at a given frame. If no unit cell is defined, returns None.

        Parameters
        ----------
        frame : int
            The frame number.

        Returns
        -------
        UnitCell or None
            The unit cell or None if no unit cells found.

        """
        self._check_frame(frame)

        if self._unit_cells is not None:
            try:
                uc = self._unit_cells[frame]
            except IndexError:
                uc = self._unit_cells[0]
            return uc

        return None

    def __len__(self) -> int:
        """Returns the length of the trajectory.

        Returns
        -------
        int
            The number of frames of the trajectory.
        """

        return self.positions.shape[0]

    def masses(self) -> npt.NDArray[float]:
        """Get masses from databases.

        Parameters
        ----------
        atom_indices : Iterable[int] or slice or int
            Atoms to get masses for. (Default: all atoms)

        Returns
        -------
        npt.NDArray[float]
            Atomic masses.
        """
        key = self.mass_key

        if key in {self.MassLoc.PER_STEP, self.MassLoc.GLOBAL}:
            masses = self._h5_file[key.value]
        else:
            masses = np.array(
                [
                    ATOMS_DATABASE.get_atom_property(at, "atomic_weight")
                    for at in self.chemical_system.atom_list
                ]
            )

        return masses.astype(np.float64)

    def has_variable(self, variable: str) -> bool:
        """Check if the trajectory has a specific variable e.g. velocities.

        Parameters
        ----------
        variable : str
            The variable to check the existence of.

        Returns
        -------
        bool
            True if variable exists.

        """
        return variable in self._h5_file["/particles/all"]

    def get_atom_property(
        self, atom_symbol: str, atom_property: str
    ) -> int | float | complex | str:
        """Get the value of atom property for the atom type.

        Parameters
        ----------
        atom_symbol : str
            Atom type.
        atom_property : str
            Name of the atom property.

        Returns
        -------
        int | float | complex | str
            Value of the atom property as defined in the atom database.

        """
        return ATOMS_DATABASE.get_atom_property(atom_symbol, atom_property)

    def atoms_in_database(self) -> list[str]:
        """Return the names of atoms defined in the atom property database.

        Here, it defaults to the central atom property database.

        Returns
        -------
        list[str]
            List of atom names that are present in the atom database.

        """
        return ATOMS_DATABASE.atoms

    def properties(self) -> list[str]:
        """Return the list of atom properties provided by the trajectory.

        Here, it defaults to the central atom property database.

        Returns
        -------
        list[str]
            List of atom property names that can be accessed.

        """
        return ATOMS_DATABASE.properties

    def variable(self, name: str) -> h5py.Dataset:
        """Return the dataset corresponding to a trajectory variable called 'name'."""
        try:
            grp = self._h5_file[f"/particles/all/{name}/value"]
        except KeyError:
            grp = self._h5_file[f"/particles/all/{name}"]

        return grp

    def variables(self) -> list[str]:
        """Return the names of available variables.

        Returns
        -------
        list[str]
            List of variables present in the file.

        """
        grp = self._h5_file["/particles/all"]
        return list(grp.keys())
