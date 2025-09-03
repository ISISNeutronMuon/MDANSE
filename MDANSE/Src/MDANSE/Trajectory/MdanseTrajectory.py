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
from pathlib import Path

import h5py
import numpy as np
import numpy.typing as npt
from more_itertools import first

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Chemistry.Databases import str_to_num
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
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


class MdanseTrajectory(TrajectoryFile):
    """Reads the MDANSE .mdt trajectory (HDF5).

    Trajectory is a wrapper object, and MdanseTrajectory
    is the specific implementation for the Mdanse HDF5 format.
    """

    def __init__(self, h5_filename: Path | str):
        """Open the file and build a trajectory.

        Parameters
        ----------
        h5_filename : Path or str
            Path to the trajectory file.

        """
        self.warned_about_complex_numbers = False
        self._property_map = {}
        self._data_types = {}
        self._data_units = {}
        self._property_cache = {}

        self.unit_cell_warning = ""
        self._h5_filename = Path(h5_filename)

        self._h5_file = h5py.File(self._h5_filename, "r")
        self._has_database = "atom_database" in self._h5_file
        self._has_atoms = []

        # Load the chemical system
        self._chemical_system = ChemicalSystem(self._h5_filename.stem, self)
        self._chemical_system.load(self._h5_file)

        # Load all the unit cells
        self._load_unit_cells()

    @classmethod
    def file_is_right(cls, filename: Path | str) -> bool:
        """Check if the input file is likely to be an .mdt trajectory.

        Parameters
        ----------
        filename : Path | str
            File to check.

        Returns
        -------
        bool
            Whether file should be loaded as .mdt.

        """
        filename = Path(filename)

        try:
            file_object = h5py.File(filename)
        except Exception as err:
            LOG.warning(f"Could not load {filename} as h5py. \nReason: {err!s}")
            return False

        try:
            mdtraj = cls(filename)
            chem = ChemicalSystem(filename.stem, mdtraj)
            chem.load(filename)
        except Exception:
            LOG.warning(
                f"Could not load ChemicalSystem from {filename}. MDANSE will try"
                " to read it as H5MD next.",
            )
            return False

        try:
            grp = file_object["/composition"]
            grp.attrs["name"]
        except KeyError:
            LOG.warning(
                f"Could not find /composition from {filename}. MDANSE will try"
                " to read it as H5MD next.",
            )
            return False

        file_object.close()

        return True

    def close(self) -> None:
        """Close the trajectory."""
        self._h5_file.close()

    def __getitem__(self, frame: int) -> dict[str, npt.NDArray[float]]:
        """Return the atom configuration for a specific frame.

        Parameters
        ----------
        frame : int
            index of a simulation frame

        Returns
        -------
        dict[str, npt.NDArray[float]]
            Atom configuration, with unit cell (if defined)

        """
        self._check_frame(frame)

        grp = self._h5_file["/configuration"]
        configuration = {k: v[frame].astype(np.float64) for k, v in grp.items()}

        for k in ("/time", "/unit_cell"):
            if k in self._h5_file:
                configuration[k.strip("/")] = self._h5_file[k][frame].astype(np.float64)

        return configuration

    def charges(self, frame: int) -> npt.NDArray[float]:
        """Return the electrical charge array for given time step.

        Parameters
        ----------
        frame : int
            frame (time step) index

        Returns
        -------
        np.ndarray
            array of float values of partial charges

        Raises
        ------
        IndexError
            if the requested frame is not in the file

        """
        self._check_frame(frame)

        if "/charge" in self._h5_file:
            return self._h5_file["/charge"].astype(np.float64)

        if "/configuration/charges" in self._h5_file:
            return self._h5_file["/configuration/charges"][frame].astype(np.float64)

        LOG.debug(f"No charge information in trajectory {self._h5_filename}")
        return np.zeros(self.chemical_system.number_of_atoms, dtype=np.float64)

    def coordinates(
        self, frame: slice | int, indices: slice | int = np.s_[:]
    ) -> npt.NDArray[float]:
        """Return the atom position array for given time step.

        Parameters
        ----------
        frame : int or slice
            Frame (time step) index.
        atom_indices : int or slice
            Atoms to select.

        Returns
        -------
        np.ndarray
            array of float values of atom coordinates

        Raises
        ------
        IndexError
            if the requested frame is not in the file

        """
        self._check_frame(frame)

        grp = self._h5_file["/configuration"]

        return grp["coordinates"][frame, indices, :].astype(np.float64)

    def configuration(
        self,
        frame: int = 0,
    ) -> RealConfiguration | PeriodicRealConfiguration:
        """Return the atom configuration for a specific frame.

        Parameters
        ----------
        frame : int
            index of a simulation frame

        Returns
        -------
        Union[RealConfiguration, PeriodicRealConfiguration]
            Atom configuration, with unit cell (if defined)

        """
        self._check_frame(frame)

        unit_cell = self._unit_cells[frame] if self._unit_cells is not None else None

        variables = {
            k: v[frame, :, :].astype(np.float64)
            for k, v in self._h5_file["configuration"].items()
            if k != "charges"
        }

        coordinates = variables.pop("coordinates")

        if unit_cell is None:
            conf = RealConfiguration(self._chemical_system, coordinates, **variables)
        else:
            conf = PeriodicRealConfiguration(
                self._chemical_system,
                coordinates,
                unit_cell,
                **variables,
            )

        return conf

    def _load_unit_cells(self):
        """Load all the unit cells."""
        if "unit_cell" in self._h5_file:
            self._unit_cells = [UnitCell(uc) for uc in self._h5_file["unit_cell"][:]]
        else:
            self._unit_cells = None
            self.unit_cell_warning = NO_CELL

        if not self.unit_cell_warning:
            if self._unit_cells[0].volume < CELL_SIZE_LIMIT:
                self.unit_cell_warning = BAD_CELL
                return

            reference_array = self._unit_cells[0].direct

            if any(
                not np.allclose(reference_array, uc.direct)
                for uc in self._unit_cells[1:]
            ):
                self.unit_cell_warning = CHANGING_CELL
                return

    def time(self):
        """Return the time array for all the frames."""
        return self._h5_file["time"][:]

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
        self._check_frame(frame)

        if self._unit_cells is not None:
            return self._unit_cells[frame]
        return None

    def __len__(self) -> int:
        """Return the length of the trajectory.

        Returns
        -------
        int
            The number of frames of the trajectory.

        """
        grp = self._h5_file["/configuration"]

        return grp["coordinates"].shape[0]

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
        try:
            masses = self.chemical_system.atom_property("atomic_weight")
        except KeyError:
            masses = [
                ATOMS_DATABASE.get_atom_property(at, "atomic_weight")
                for at in self.chemical_system.atom_list
            ]

        return np.array(masses).astype(np.float64)

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
        return variable in self._h5_file["/configuration"]

    def get_atom_property(
        self,
        atom_symbol: str,
        atom_property: str,
    ) -> float | int | complex | str:
        """Get the value of a property for an atom type.

        The priority is given to the values stored in the trajectory file.
        If the atom property or type are not included in the trajectory,
        they will be taken from the central database instead.

        Parameters
        ----------
        atom_symbol : str
            Atom type.
        atom_property : str
            Name of the property, such as mass or neutron scattering length.

        Returns
        -------
        float | int | str
            The value of the property in any format specified by the database.

        Raises
        ------
        KeyError
            If no database contained the required entry.

        """
        if not self._has_database or (
            atom_symbol not in self._has_atoms
            and atom_symbol not in self._h5_file["/atom_database"]
        ):
            return ATOMS_DATABASE.get_atom_property(atom_symbol, atom_property)

        if (
            atom_symbol not in self._has_atoms
            and atom_symbol in self._h5_file["/atom_database"]
        ):
            self._has_atoms.append(atom_symbol)

        if atom_property not in self._property_map:
            index = first(
                np.where(
                    self._h5_file["/atom_database/property_labels"][:]
                    == atom_property.encode("utf-8"),
                )[0],
                None,
            )

            if index is None:
                if atom_property != "dummy":
                    raise KeyError(
                        f"Property {atom_property} is not in the trajectory's"
                        " internal database.",
                    )

                try:
                    return ATOMS_DATABASE.get_atom_property(atom_symbol, atom_property)
                except KeyError:
                    if (
                        "_" in atom_symbol
                    ):  # this is most likely an artificial atom from a molecule
                        return 0  # the molecule atoms are not dummy

            self._property_map[atom_property] = index

        index = self._property_map[atom_property]
        if index not in self._data_types:
            self._data_types[index] = self._h5_file["/atom_database/property_types"][
                index
            ]

        data_type = self._data_types[index]

        if index not in self._data_units:
            data_unit = "none"
            try:
                unit_lookup = self._h5_file["/atom_database/property_units"]
            except KeyError:
                if not self.warned_about_complex_numbers:
                    LOG.warning(
                        "This trajectory file was generated with old MDANSE. If you "
                        "need complex b, please generate it again.",
                    )
                    self.warned_about_complex_numbers = True
            else:
                data_unit = unit_lookup[index]
            self._data_units[index] = data_unit
        data_unit = self._data_units[index]

        if (atom_symbol, index) not in self._property_cache:
            value = self._h5_file[f"/atom_database/{atom_symbol}"][index]
            if data_type != b"complex":
                value = value.real
            self._property_cache[(atom_symbol, index)] = value

        value = self._property_cache[(atom_symbol, index)]

        if atom_property == "color":
            value = str_to_num(value)
            out = ";".join(map(str, int(value).to_bytes(3, "big")))

        elif data_type == b"int":
            out = int(value)

        elif data_type == b"str":
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            out = value

        else:
            out = str_to_num(value)
            unit_conv = {
                b"fm": "ang",
                b"barn": "ang2",
            }
            if data_unit in unit_conv:
                out = measure(out, data_unit.decode("utf-8")).toval(
                    unit_conv[data_unit]
                )

        return out

    def atoms_in_database(self) -> list[str]:
        """Return the list of all the atom types in trajectory's database.

        Returns
        -------
        list[str]
            List of atom type names.

        """
        if "atom_database" not in self._h5_file:
            return ATOMS_DATABASE.atoms
        return [
            key
            for key in self._h5_file["/atom_database"].keys()
            if "property_" not in key
        ]

    def properties(self) -> list[str]:
        """Return the list of all the properties in the trajectory's database.

        Returns
        -------
        list[str]
            List of valid atom property names.

        """
        if "atom_database" not in self._h5_file:
            return ATOMS_DATABASE.properties
        return [
            label.decode("utf-8")
            for label in self._h5_file["/atom_database/property_labels"]
        ]

    def variable(self, name: str):
        """Return a specific dataset corresponding to a variable called 'name'."""
        return self._h5_file["/configuration/" + name]

    def variables(self) -> list[str]:
        """Return the configuration variables stored in this trajectory.

        Returns
        -------
        list[str]
            The configuration keys.

        """
        grp = self._h5_file["/configuration"]

        return list(grp.keys())
