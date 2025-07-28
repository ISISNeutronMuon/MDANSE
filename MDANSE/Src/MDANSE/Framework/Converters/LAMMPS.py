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
from collections import defaultdict
from enum import Enum, auto
from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

import h5py
import numpy as np
from more_itertools import consume as drop
from more_itertools import ilen, take
from numpy.typing import NDArray

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    PeriodicRealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.ConfigFileConfigurator import (
        ConfigFileConfigurator,
    )

ELECTRON_CHARGE = 1.6021765e-19
DIMS = ("x", "y", "z")

LAMMPS_UNITS = {
    "real": {
        "energy": "kcal_per_mole",
        "time": "fs",
        "length": "ang",
        "velocity": "ang/fs",
        "mass": "Da",
        "charge_conv": 1.0,
    },
    "metal": {
        "energy": "eV",
        "time": "ps",
        "length": "ang",
        "velocity": "ang/ps",
        "mass": "Da",
        "charge_conv": 1.0,
    },
    "si": {
        "energy": "J",
        "time": "s",
        "length": "m",
        "velocity": "m/s",
        "mass": "kg",
        "charge_conv": 1.0 / ELECTRON_CHARGE,
    },
    "cgs": {
        "energy": "erg",  # this will fail
        "time": "s",
        "length": "cm",
        "velocity": "cm/s",
        "mass": "g",
        "charge_conv": 1.0 / 4.8032044e-10,
    },
    "electron": {
        "energy": "Ha",
        "time": "fs",
        "length": "Bohr",
        "velocity": "ang/fs",
        "mass": "Da",
        "charge_conv": 1.0,
    },
    "micro": {
        "energy": "pg*m/s",
        "time": "us",
        "length": "um",
        "velocity": "m/s",
        "mass": "pg",
        "charge_conv": 1.0 / (ELECTRON_CHARGE * 1e12),
    },
    "nano": {
        "energy": "ag*m/s",
        "time": "ns",
        "length": "nm",
        "velocity": "m/s",
        "mass": "ag",
        "charge_conv": 1.0,
    },
}

UnitSchemes = Literal["real", "metal", "si", "cgs", "electron", "micro", "nano"]


class LAMMPSTrajectoryFileError(Error):
    pass


class BoxStyle(Enum):
    """Different styles of "box" provided by LAMMPS.

    Handles conversion to standard 3x3 lattice vectors.
    """

    ORTHOGONAL = auto()
    NONORTHOGONAL = auto()
    TRICLINIC = auto()

    def to_cell(
        self, value: NDArray[float], *, bounds: bool = False
    ) -> tuple[NDArray[float], NDArray[float]]:
        """Convert from LAMMPS box definition to unit cell, origin.

        Parameters
        ----------
        value : NDArray[float]
            LAMMPS unit cell specification.
        bounds : bool
            For LAMMPS' non-orthogonal cells dumps provide *bounds*
            rather than ``[xyz](lo|hi)``. If this is true, convert them.

        Returns
        -------
        NDArray[float]
            Unit cell as 3x3 matrix.
        NDArray[float]
            Origin as 3-vector.

        Examples
        --------
        >>> BoxStyle.ORTHOGONAL.to_cell([2, 5, 2, 5, 2, 5])
        (array([[3., 0., 0.],
               [0., 3., 0.],
               [0., 0., 3.]]), array([2., 2., 2.]))
        >>> BoxStyle.ORTHOGONAL.to_cell([[2, 5], [2, 5], [2, 5]])
        (array([[3., 0., 0.],
               [0., 3., 0.],
               [0., 0., 3.]]), array([2., 2., 2.]))
        >>> BoxStyle.NONORTHOGONAL.to_cell([[2, 5, 1], [2, 5, 2], [2, 5, 4]])
        (array([[3., 0., 0.],
               [1., 3., 0.],
               [2., 4., 3.]]), array([2., 2., 2.]))
        >>> a = BoxStyle.NONORTHOGONAL.to_cell([[-7.6875, 20.0293, 0.],
        ...                                     [0., 11.5962, -7.6875],
        ...                                     [0., 19.6804, 0.]], bounds=True)
        >>> b = BoxStyle.NONORTHOGONAL.to_cell([[0., 20.0293, 0.],
        ...                                     [0., 11.5962, -7.6875],
        ...                                     [0., 19.6804, 0.]], bounds=False)
        >>> np.allclose(a[0], b[0]), np.allclose(a[1], b[1])
        (True, True)
        >>> BoxStyle.TRICLINIC.to_cell([[1, 2, 3, 2], [4, 5, 6, 2], [7, 8, 9, 2]])
        (array([[1., 2., 3.],
               [4., 5., 6.],
               [7., 8., 9.]]), array([2., 2., 2.]))
        """
        value = np.array(value, dtype=float)
        if self is BoxStyle.ORTHOGONAL:
            value = value.reshape((3, 2))
            unit_cell, origin = np.diag(value[:, 1] - value[:, 0]), value[:, 0]
        elif self is BoxStyle.NONORTHOGONAL:
            value = value.reshape((3, 3))
            xy, xz, yz = value[:, 2]

            if bounds:
                value[0, 0] -= min(0.0, xy, xz, xy + xz)
                value[0, 1] -= max(0.0, xy, xz, xy + xz)
                value[1, 0] -= min(0.0, yz)
                value[1, 1] -= max(0.0, yz)

            unit_cell, origin = np.diag(value[:, 1] - value[:, 0]), value[:, 0]
            unit_cell[1, 0] = xy
            unit_cell[2, 0] = xz
            unit_cell[2, 1] = yz
        elif self is BoxStyle.TRICLINIC:
            value = value.reshape((3, 4))
            unit_cell, origin = value[:3, :3], value[:, 3]

        return unit_cell, origin


class LAMMPSReader(ABC):
    """Abstract class for reading various LAMMPS files."""

    def __init__(
        self,
        *_args,
        fold_coordinates: bool = False,
        timestep: float = 1.0,
        lammps_units: str = "real",
        **_kwargs,
    ):
        self._units = lammps_units
        self.units = LAMMPS_UNITS[lammps_units]
        self._timestep = timestep
        self._fold = fold_coordinates
        self._file = None

    @staticmethod
    def _add_bonds(config, chemical_system):
        if config["n_bonds"]:
            bonds = [(idx1 - 1, idx2 - 1) for idx1, idx2 in config["bonds"]]
            chemical_system.add_bonds(bonds)

    def close(self):
        """Close contained file when done reading."""
        try:
            self._file.close()
        except Exception:
            LOG.error(f"Could not close file: {self._file}")

    def set_output(self, output_trajectory: TrajectoryWriter) -> None:
        """Redirect output to the given tractory file."""
        self._trajectory = output_trajectory

    def set_units(self, units: UnitSchemes) -> None:
        """Set unit scheme.

        Parameters
        ----------
        units : UnitSchemes
            Scheme to set.
        """
        self.units = LAMMPS_UNITS[units]

    @staticmethod
    @abstractmethod
    def get_time_steps(filename: Path | str) -> int:
        """Get number of timesteps in file.

        Parameters
        ----------
        filename : Path | str
            File to parse.

        Returns
        -------
        int
            Number of timesteps found.
        """

    @abstractmethod
    def open_file(self, filename: Path | str) -> None:
        """Open file for reading as LAMMPS format.

        Parameters
        ----------
        filename : Path | str
            File to open for reading.
        """

    @abstractmethod
    def parse_first_step(
        self, aliases: dict[str, dict[str, str]], config: dict[str, Any]
    ):
        """Parse first step to determine output sizes and data.

        Parameters
        ----------
        aliases : dict[str, dict[str, str]]
            Mapping of atomic aliases to elements.
        config : dict[str, Any]
            Configurations details.

        Raises
        ------
        LAMMPSTrajectoryFileError
            If file invalid.
        """


class LAMMPScustom(LAMMPSReader):
    """Parse LAMMPS custom dump format.

    Raises
    ------
    LAMMPSTrajectoryFileError
        If file is invalid.

    Notes
    -----
    Does not support:
    - Multiple different `dump`s in the same file.
    - Multiple runs in the same file.
    - Vector computes as `c_x[*]` in dump.
    - Variable numbers of atoms or atom_types
    """

    #: Type mapping for lammps custom dumps. Return the float **class** by default.
    _type_map = defaultdict(
        lambda: float,
        id=int,
        mol=int,
        proc=int,
        procp1=int,
        type=int,
        typelabel=str,
        element=str,
        ix=int,
        iy=int,
        iz=int,
        index=int,
        gname=str,
        dname=str,
    )

    @staticmethod
    def get_time_steps(filename: Path | str) -> int:
        """Get number of timesteps in file.

        Parameters
        ----------
        filename : Path | str
            File to parse.

        Returns
        -------
        int
            Number of timesteps found.
        """
        with open(filename, encoding="utf-8") as file:
            return ilen(filter(lambda line: line.startswith("ITEM: TIMESTEP"), file))

    def open_file(self, filename: Path | str) -> None:
        """Open file for reading as LAMMPS custom format.

        Parameters
        ----------
        filename : Path | str
            File to open for reading.
        """
        self._file = open(filename, encoding="utf-8")
        self._start = 0

    def parse_first_step(
        self, aliases: dict[str, dict[str, str]], config: dict[str, Any]
    ) -> ChemicalSystem:
        """Parse first step to determine output sizes and data.

        Parameters
        ----------
        aliases : dict[str, dict[str, str]]
            Mapping of atomic aliases to elements.
        config : dict[str, Any]
            Configurations details.

        Returns
        -------
        ChemicalSystem
            Initialised structure.

        Raises
        ------
        LAMMPSTrajectoryFileError
            If file invalid.
        """
        self._item_location = {}

        chemical_system = ChemicalSystem()

        file = enumerate(iter(self._file))

        for curr_line, line in file:
            if not line:
                break

            if line.startswith("ITEM: TIMESTEP"):
                self._item_location["TIMESTEP"] = (curr_line + 1, curr_line + 2)

            elif line.startswith("ITEM: BOX BOUNDS"):
                style = line.removeprefix("ITEM: BOX BOUNDS").split()

                if len(style) in (0, 3):  # "xx yy zz"
                    self._style = BoxStyle.ORTHOGONAL
                elif len(style) == 6:  # "xy xz yz xx yy zz"
                    self._style = BoxStyle.NONORTHOGONAL
                elif len(style) == 2:  # "abc origin"
                    self._style = BoxStyle.TRICLINIC
                else:
                    raise LAMMPSTrajectoryFileError(f"Unrecognised style {line!r}")

                self._item_location["BOX BOUNDS"] = (curr_line + 1, curr_line + 4)

            elif line.startswith("ITEM: NUMBER OF ATOMS"):
                _, n_atoms = next(file)
                self._nAtoms = int(n_atoms)

            elif line.startswith("ITEM: ATOMS"):
                self.keywords = dict(zip(line.split()[2:], count()))

                self._charge = "q" in self.keywords
                self._image = any(f"i{dim}" in self.keywords for dim in DIMS)

                for i in ("", "u", "s", "su"):
                    if all(f"{dim}{i}" in self.keywords for dim in DIMS):
                        self.keywords["pos"] = tuple(f"{dim}{i}" for dim in DIMS)
                        self._fractionalCoordinates = "s" in i
                        self._unwrappedCoordinates = "u" in i
                        break
                else:
                    raise LAMMPSTrajectoryFileError(
                        "No coordinates could be found in the trajectory"
                    )

                for key in ("v", "f"):
                    if all(f"{key}{dim}" in self.keywords for dim in DIMS):
                        self.keywords[key] = tuple(f"{key}{dim}" for dim in DIMS)

                self._rankToName = {}
                element_list = []
                name_list = []
                index_list = []

                self._item_location["ATOMS"] = (
                    curr_line + 1,
                    curr_line + self._nAtoms + 1,
                )

                for i, (_, atom_line) in enumerate(take(self._nAtoms, file)):
                    temp = {
                        key: self._type_map[key](val)
                        for key, val in zip(self.keywords, atom_line.split())
                    }
                    idx = temp.get("id", 1)

                    try:
                        atom_type = temp.get("type")
                        if atom_type is None:
                            atom_type = config["atom_types"][i]
                    except IndexError:
                        LOG.error(
                            f"Failed to find index [{i}] in list of len {len(config['atom_types'])}"
                        )
                        raise

                    label = config["elements"][atom_type]
                    mass = config["mass"][atom_type - 1]  # Mass is array, 0-indexed

                    name = f"{label}_{idx:d}"
                    temp_index = temp.get("index", i)
                    self._rankToName[temp_index] = name

                    element = get_element_from_mapping(aliases, label, mass=mass)

                    element_list.append(element)
                    name_list.append(str(atom_type))
                    index_list.append(idx)

                sorting = np.argsort(index_list)
                chemical_system.initialise_atoms(
                    np.array(element_list)[sorting], np.array(name_list)[sorting]
                )

                self._add_bonds(config, chemical_system)

                self._last = curr_line + self._nAtoms + 1

                break

        return chemical_system

    def run_step(self, index: int) -> tuple[int, int | None]:
        """Runs a single step of the conversion job.

        Parameters
        ----------
        index : int
            The index of the step.

        Notes
        -----
        The argument index is the index of the loop not the index of the frame.

        Returns
        -------
        int
            Index of frame.
        int
            Next line of file to start at.
        """
        file = iter(self._file)

        # Drop info before timestep.
        drop(file, self._item_location["TIMESTEP"][0])

        step = next(file, None)
        if step is None:
            return index, None

        time = int(step) * self._timestep * measure(1.0, self.units["time"]).toval("ps")

        drop(
            file,
            self._item_location["BOX BOUNDS"][0] - self._item_location["TIMESTEP"][1],
        )

        cell = np.fromstring(" ".join(take(3, file)), dtype=np.float64, sep=" ")
        unit_cell, origin = self._style.to_cell(cell, bounds=True)

        len_conv = measure(1.0, self.units["length"]).toval("nm")

        unit_cell *= len_conv
        unit_cell = UnitCell(unit_cell)

        drop(
            file, self._item_location["ATOMS"][0] - self._item_location["BOX BOUNDS"][1]
        )

        coords = np.empty(
            (self._trajectory.chemical_system.number_of_atoms, 3), dtype=np.float64
        )
        if "v" in self.keywords:
            velocities = np.empty(
                (self._trajectory.chemical_system.number_of_atoms, 3), dtype=np.float64
            )
        if "f" in self.keywords:
            forces = np.empty(
                (self._trajectory.chemical_system.number_of_atoms, 3), dtype=np.float64
            )

        if self._charge is not None:
            charges = np.empty(
                self._trajectory.chemical_system.number_of_atoms, dtype=np.float64
            )

        for i, line in enumerate(take(self._nAtoms, file), 1):
            temp = {
                key: self._type_map[key](val)
                for key, val in zip(self.keywords, line.split())
            }
            idx = temp.get("id", i) - 1  # MDANSE 0-indexed
            coords[idx, :] = np.array(
                [temp[pos] for pos in self.keywords["pos"]],
                dtype=np.float64,
            )

            if "v" in self.keywords:
                velocities[idx, :] = np.array(
                    [temp[pos] for pos in self.keywords["v"]],
                    dtype=np.float64,
                )

            if "f" in self.keywords:
                forces[idx, :] = np.array(
                    [temp[pos] for pos in self.keywords["f"]],
                    dtype=np.float64,
                )

            if "q" in temp:
                charges[idx] = self._type_map["q"](temp["q"])

            if not self._unwrappedCoordinates and self._image:
                if self._fractionalCoordinates:
                    for ind, dim in enumerate(DIMS):
                        coords[idx, ind] += temp.get(f"i{dim}", 0)
                else:
                    for ind, dim, vec in zip(count(), DIMS, unit_cell.direct):
                        coords[idx, ind] += temp.get(f"i{dim}", 0.0) * vec

        if self._fractionalCoordinates:
            # MDANSE origin is always 0,0,0
            origin *= len_conv
            origin_recip = np.matmul(origin, unit_cell.inverse)

            coords -= origin_recip

            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system, coords, unit_cell
            )

            real_conf = conf.to_real_configuration()

        else:
            # MDANSE origin is always 0,0,0
            coords -= origin
            coords *= len_conv

            real_conf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, coords, unit_cell
            )

        if self._fold:
            # The whole configuration is folded in to the simulation box.
            real_conf.fold_coordinates()

        if "v" in self.keywords:
            real_conf["velocities"] = velocities
        if "f" in self.keywords:
            real_conf["gradients"] = forces

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            real_conf,
            time,
            units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
        )

        if self._charge:
            self._trajectory.write_charges(charges * self.units["charge_conv"], index)

        self._start += self._last

        return index, self._start


class LAMMPSxyz(LAMMPSReader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._full_cell = None

    @staticmethod
    def get_time_steps(filename: Path | str) -> int:
        """Get number of timesteps in file.

        Parameters
        ----------
        filename : Path | str
            File to parse.

        Returns
        -------
        int
            Number of timesteps found.
        """
        with open(filename, encoding="utf-8") as file:
            return sum(1 for line in file if len(line.split()) == 1)

    def open_file(self, filename: Path | str) -> None:
        """Open file for reading as LAMMPS custom format.

        Parameters
        ----------
        filename : Path | str
            File to open for reading.
        """
        self._file = open(filename, encoding="utf-8")

    def read_step(self) -> tuple[int, NDArray[int], NDArray[float]]:
        """Read an XYZ file step.

        Returns
        -------
        int
            Current timestep.
        NDArray[int]
            Atom type indices.
        NDArray[float]
            Atomic positions.
        """
        line = self._file.readline()
        number_of_atoms = int(line)
        line = self._file.readline()
        timestep = int(line.rsplit(maxsplit=1)[-1])

        positions = np.empty((number_of_atoms, 3), dtype=np.float64)
        atom_types = np.empty(number_of_atoms, dtype=int)

        for ind, line in enumerate(take(number_of_atoms, self._file)):
            if not line:
                break

            atom_types[ind], *positions[ind, :] = line.split()

        return timestep, atom_types, positions

    def parse_first_step(
        self, aliases: dict[str, dict[str, str]], config: dict[str, Any]
    ) -> ChemicalSystem:
        """Parse first step to determine output sizes and data.

        Parameters
        ----------
        aliases : dict[str, dict[str, str]]
            Mapping of atomic aliases to elements.
        config : dict[str, Any]
            Configurations details.

        Returns
        -------
        ChemicalSystem
            Initialised structure.

        Raises
        ------
        LAMMPSTrajectoryFileError
            If file invalid.
        """
        _, atom_types, positions = self.read_step()

        self._nAtoms = len(atom_types)

        self._fractionalCoordinates = False
        unit_cell = config["unit_cell"]

        span = np.max(positions, axis=0) - np.min(positions, axis=0)
        cellspan = np.linalg.norm(unit_cell, axis=1)

        if np.allclose(cellspan, [0, 0, 0]):
            self._fractionalCoordinates = False
            full_cell = None

        elif np.allclose(span, [1.0, 1.0, 1.0], rtol=0.1, atol=0.1):
            self._fractionalCoordinates = not np.allclose(
                cellspan, [1.0, 1.0, 1.0], rtol=0.1, atol=0.1
            )
            full_cell = unit_cell * measure(1.0, self.units["length"]).toval("nm")

        else:
            self._fractionalCoordinates = False
            multiplicity = np.round(np.abs(span / cellspan)).astype(int)
            full_cell = unit_cell * multiplicity.reshape((3, 1))
            full_cell *= measure(1.0, self.units["length"]).toval("nm")

        self._full_cell = full_cell

        self._rankToName = {}
        element_list = []
        name_list = []
        chemical_system = ChemicalSystem()

        for idx in range(self._nAtoms):
            atom_type = atom_types[idx]
            label = config["elements"][atom_type]
            mass = config["mass"][atom_type - 1]
            name = f"{label}_{idx:d}"
            self._rankToName[idx] = name

            element_list.append(get_element_from_mapping(aliases, label, mass=mass))
            name_list.append(str(atom_type + 1))

        chemical_system.initialise_atoms(element_list, name_list)

        self._add_bonds(config, chemical_system)

        return chemical_system

    def run_step(self, index) -> tuple[int, int | None]:
        """Runs a single step of the conversion job.

        Parameters
        ----------
        index : int
            The index of the step.

        Notes
        -----
        The argument index is the index of the loop not the index of the frame.

        Returns
        -------
        int
            Index of frame.
        int
            Next line of file to start at.
        """

        try:
            timestep, _, positions = self.read_step()
        except ValueError:
            return index, None

        unit_cell = UnitCell(self._full_cell)
        time = timestep * self._timestep * measure(1.0, self.units["time"]).toval("ps")

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system, positions, unit_cell
            )
            real_conf = conf.to_real_configuration()
        else:
            positions *= measure(1.0, self.units["length"]).toval("nm")
            real_conf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, positions, unit_cell
            )

        if self._fold:
            # The whole configuration is folded in to the simulation box.
            real_conf.fold_coordinates()

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            real_conf,
            time,
            units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
        )

        return index, 0


class LAMMPSh5md(LAMMPSReader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._charges_fixed = None
        self._charges_variable = None

    @staticmethod
    def get_time_steps(filename: Path | str) -> int:
        """Get number of timesteps in file.

        Parameters
        ----------
        filename : Path | str
            File to parse.

        Returns
        -------
        int
            Number of timesteps found.
        """
        with h5py.File(filename, "r") as file:
            return len(file["/particles/all/position/time"])

    def open_file(self, filename: Path | str):
        """Open file for reading as LAMMPS h5md format.

        Parameters
        ----------
        filename : Path | str
            File to open for reading.
        """
        self._file = h5py.File(filename, "r")

    def parse_first_step(
        self, aliases: dict[str, dict[str, str]], config: ConfigFileConfigurator
    ) -> ChemicalSystem:
        """Parse first step to determine output sizes and data.

        Parameters
        ----------
        aliases : dict[str, dict[str, str]]
            Mapping of atomic aliases to elements.
        config : ConfigFileConfigurator
            Configurations details.

        Returns
        -------
        ChemicalSystem
            Initialised structure.

        Raises
        ------
        LAMMPSTrajectoryFileError
            If file invalid.
        """
        try:
            atom_types = self._file["/particles/all/species/value"][0]
        except KeyError:
            atom_types = config["atom_types"]

        self._nAtoms = len(self._file["/particles/all/position/value"][0])

        if len(atom_types) < self._nAtoms:
            atom_types = int(round(self._nAtoms / len(atom_types))) * list(atom_types)

        self._fractionalCoordinates = False
        cell_edges = self._file["/particles/all/box/edges/value"][0]

        self._full_cell = np.diag(cell_edges)
        self._full_cell *= measure(1.0, self.units["length"]).toval("nm")

        try:
            self._charges_fixed = self._file["/particles/all/charge"][:]
        except Exception:
            pass

        self._rankToName = {}
        chemical_system = ChemicalSystem()
        element_list = []
        name_list = []

        for idx in range(self._nAtoms):
            atom_type = atom_types[idx]
            label = config["elements"][atom_type]
            mass = config["mass"][atom_type - 1]
            name = f"{label}_{idx:d}"
            self._rankToName[idx] = name

            element_list.append(get_element_from_mapping(aliases, label, mass=mass))
            name_list.append(str(atom_type + 1))

        chemical_system.initialise_atoms(element_list, name_list)

        self._add_bonds(config, chemical_system)

        return chemical_system

    def run_step(self, index: int) -> tuple[int, int]:
        """Runs a single step of the conversion job.

        Parameters
        ----------
        index : int
            The index of the step.

        Notes
        -----
        The argument index is the index of the loop not the index of the frame.

        Returns
        -------
        int
            Index of frame.
        int
            Next line of file to start at.
        """
        positions = self._file["/particles/all/position/value"][index]
        timestep = self._file["/particles/all/position/step"][index]

        unit_cell = UnitCell(self._full_cell)
        time = timestep * self._timestep * measure(1.0, self.units["time"]).toval("ps")

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system, positions, unit_cell
            )
            real_conf = conf.to_real_configuration()
        else:
            positions *= measure(1.0, self.units["length"]).toval("nm")
            real_conf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, positions, unit_cell
            )

        if self._fold:
            # The whole configuration is folded in to the simulation box.
            real_conf.fold_coordinates()

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            real_conf,
            time,
            units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
        )
        if self._charges_fixed is None:
            try:
                charge = self._file["/particles/all/charge/value"][index]
            except Exception:
                pass
            else:
                self._trajectory.write_charges(
                    charge * self.units["charge_conv"], index
                )

        return index, 0


class LAMMPS(Converter):
    """Converts a LAMMPS trajectory to an MDT trajectory."""

    label = "LAMMPS"

    _READERS = {
        "custom": LAMMPScustom,
        "xyz": LAMMPSxyz,
        "h5md": LAMMPSh5md,
    }

    settings = {}
    settings["config_file"] = (
        "ConfigFileConfigurator",
        {
            "label": "LAMMPS configuration file",
            "wildcard": "All files (*);;Config files (*.config)",
            "default": "INPUT_FILENAME.config",
        },
    )
    settings["trajectory_file"] = (
        "InputFileConfigurator",
        {
            "label": "LAMMPS trajectory file",
            "wildcard": "All files (*);;XYZ files (*.xyz);;H5MD files (*.h5);;lammps files (*.lammps)",
            "default": "INPUT_FILENAME.lammps",
        },
    )
    settings["trajectory_format"] = (
        "SingleChoiceConfigurator",
        {
            "label": "LAMMPS trajectory format",
            "choices": ["custom", "xyz", "h5md"],
            "default": "custom",
        },
    )
    settings["lammps_units"] = (
        "SingleChoiceConfigurator",
        {
            "label": "LAMMPS unit system",
            "choices": [
                "From config",
                "real",
                "metal",
                "si",
                "cgs",
                "electron",
                "micro",
                "nano",
            ],
            "default": "real",
        },
    )
    settings["atom_type"] = (
        "SingleChoiceConfigurator",
        {
            "label": "LAMMPS atom type",
            "choices": [
                "From config",
                "angle",
                "atomic",
                "body",
                "bond",
                "bpm/sphere",
                "charge",
                "dielectric",
                "dipole",
                "dpd",
                "edpd",
                "electron",
                "ellipsoid",
                "full",
                "hybrid",
                "line",
                "mdpd",
                "molecular",
                "peri",
                "rheo",
                "rheo/thermal",
                "smd",
                "sph",
                "sphere",
                "spin",
                "tdpd",
                "template",
                "tri",
                "wavepacket",
            ],
            "default": "From config",
        },
    )

    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "config_file"},
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {
            "label": "Time step (lammps units, depends on unit system)",
            "default": 1.0,
            "mini": 1.0e-9,
        },
    )
    settings["n_steps"] = (
        "IntegerConfigurator",
        {
            "label": "Number of time steps (0 for automatic detection)",
            "default": 0,
            "mini": 0,
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates in to box"},
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "config_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self._lammpsConfig = self.configuration["config_file"]

        self._lammps_units = self.configuration["lammps_units"]["value"]
        self._atom_type = self.configuration["atom_type"]["value"]

        if self._lammps_units == "From config":
            if "units" not in self._lammpsConfig:
                raise KeyError("Units not found in lammps config")
            self._lammps_units = self._lammpsConfig["units"]

        self._lammps_format = self.configuration["trajectory_format"]["value"]

        self._reader = self.create_reader(self._lammps_format)

        self._reader.set_units(self._lammps_units)
        self._chemical_system = self.parse_first_step(self._atomicAliases)
        self._chemical_system.find_clusters_from_bonds()

        if self.numberOfSteps == 0:
            self.numberOfSteps = self._reader.get_time_steps(
                self.configuration["trajectory_file"]["value"]
            )

        charges_single_cell = self._lammpsConfig["charges"]
        charges_single_cell *= self._reader.units["charge_conv"]

        # Assume replicate
        if len(charges_single_cell) < self._chemical_system.number_of_atoms:
            charges = list(charges_single_cell) * int(
                self._chemical_system.number_of_atoms // len(charges_single_cell)
            )
        else:
            charges = list(charges_single_cell)

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
            initial_charges=charges,
        )

        self._start = 0
        self._reader.open_file(self.configuration["trajectory_file"]["value"])
        self._reader.set_output(self._trajectory)

    def create_reader(
        self, trajectory_type: Literal["custom", "xyz", "h5md"]
    ) -> LAMMPSReader:
        """Create the required reader.

        Parameters
        ----------
        trajectory_type : Literal["custom", "xyz", "h5md"]
            Type of file to load.

        Returns
        -------
        LAMMPSReader
            Configured reader.
        """
        return self._READERS[trajectory_type](
            lammps_units=self._lammps_units,
            atom_type=self._atom_type,
            timestep=self.configuration["time_step"]["value"],
            fold_coordinates=self.configuration["fold"]["value"],
        )

    def run_step(self, index) -> tuple[int, None]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int.
            The index of the step.

        Returns
        -------
        int
            Index of job step.
        """

        val1, val2 = self._reader.run_step(index)

        self._start = val2

        return val1, None

    def combine(self, index: int, x: Any) -> None:
        """No work to be done.

        Parameters
        ----------
        index : int.
            The index of the step.
        x : Any
            Data.
        """

    def finalize(self) -> None:
        """
        Finalize the job.
        """

        self._reader.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()

    def parse_first_step(self, aliases: dict[str, dict[str, str]]) -> ChemicalSystem:
        """Wrapper for `parse_first_step` on readers.

        Parameters
        ----------
        aliases : dict[str, dict[str, str]]
            Mapping of atomic aliases to elements.

        Returns
        -------
        ChemicalSystem
            Initialised structure.

        See Also
        --------
        LAMMPScustom.parse_first_step
        LAMMPSxyz.parse_first_step
        LAMMPSh5md.parse_first_step
        """

        self._reader.open_file(self.configuration["trajectory_file"]["value"])
        chemical_system = self._reader.parse_first_step(aliases, self._lammpsConfig)
        self._reader.close()
        return chemical_system
