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
from pathlib import Path
from typing import Union

import h5py
import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
    contiguous_coordinates_real,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import (
    atomic_trajectory,
)
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class MdanseTrajectory:
    """Reads the MDANSE .mdt trajectory (HDF5).

    Trajectory is a wrapper object, and MdanseTrajectory
    is the specific implementation for the Mdanse HDF5 format.
    """

    def __init__(self, h5_filename: Union[Path, str]):
        """Open the file and build a trajectory.

        Parameters
        ----------
        h5_filename : Union[Path, str]
            path to the trajectory file

        """
        self.warned_about_complex_numbers = False
        self._property_map = {}
        self._data_types = {}
        self._property_cache = {}

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
    def file_is_right(self, filename: Union[Path, str]):
        """Check if the input file is likely to be an .mdt trajectory."""
        filename = Path(filename)
        result = True
        try:
            file_object = h5py.File(filename)
        except Exception:
            result = False
        else:
            try:
                with MdanseTrajectory(filename) as mdtraj:
                    chem = ChemicalSystem(file_object, mdtraj)
                    chem.load(filename)
            except Exception:
                LOG.warning(
                    f"Could not load ChemicalSystem from {filename}. MDANSE will try to read it as H5MD next."
                )
                result = False
            else:
                return True
            try:
                grp = file_object["/composition"]
                _ = grp.attrs["name"]
            except KeyError:
                LOG.warning(
                    f"Could not find /composition from {filename}. MDANSE will try to read it as H5MD next."
                )
                result = False
            else:
                result = True
            file_object.close()
        return result

    def close(self):
        """Close the trajectory."""
        self._h5_file.close()

    def __getitem__(
        self,
        frame: int,
    ) -> Union[RealConfiguration, PeriodicRealConfiguration]:
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
        grp = self._h5_file["/configuration"]
        configuration = {}
        for k, v in grp.items():
            configuration[k] = v[frame].astype(np.float64)

        for k in self._h5_file:
            if k in ("time", "unit_cell"):
                configuration[k] = self._h5_file[k][frame].astype(np.float64)

        return configuration

    def __getstate__(self):
        d = self.__dict__.copy()
        del d["_h5_file"]
        return d

    def __setstate__(self, state):
        self.__dict__ = state
        self._h5_file = h5py.File(state["_h5_filename"], "r")

    def charges(self, frame: int) -> np.ndarray:
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
        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        try:
            charges = self._h5_file["/charge"]
        except KeyError:
            try:
                charge_per_frame = self._h5_file["/configuration/charges"]
            except KeyError:
                LOG.debug(f"No charge information in trajectory {self._h5_filename}")
                charges = np.zeros(self.chemical_system.number_of_atoms)
            else:
                charges = charge_per_frame[frame]

        return charges.astype(np.float64)

    def coordinates(self, frame: int) -> np.ndarray:
        """Return the atom position array for given time step.

        Parameters
        ----------
        frame : int
            frame (time step) index

        Returns
        -------
        np.ndarray
            array of float values of atom coordinates

        Raises
        ------
        IndexError
            if the requested frame is not in the file

        """
        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        grp = self._h5_file["/configuration"]

        return grp["coordinates"][frame].astype(np.float64)

    def configuration(
        self,
        frame: int,
    ) -> Union[RealConfiguration, PeriodicRealConfiguration]:
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
        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        unit_cell = self._unit_cells[frame] if self._unit_cells is not None else None

        variables = {}
        for k, v in self._h5_file["configuration"].items():
            if k == "charges":
                continue
            variables[k] = v[frame, :, :].astype(np.float64)

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

    def time(self):
        """Return the time array for all the frames."""
        return self._h5_file["time"][:]

    def unit_cell(self, frame):
        """Return the unit cell at a given frame. If no unit cell is defined, returns None.

        :param frame: the frame number
        :type frame: int

        :return: the unit cell
        :rtype: ndarray
        """
        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        if self._unit_cells is not None:
            return self._unit_cells[frame]
        return None

    def __len__(self):
        """Return the length of the trajectory.

        :return: the number of frames of the trajectory
        :rtype: int
        """
        grp = self._h5_file["/configuration"]

        return grp["coordinates"].shape[0]

    def read_com_trajectory(
        self,
        atom_indices,
        first=0,
        last=None,
        step=1,
        *,
        box_coordinates=False,
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

        if len(atom_indices) == 1:
            return self.read_atomic_trajectory(
                atom_indices[0],
                first=first,
                last=last,
                step=step,
                box_coordinates=box_coordinates,
            )

        try:
            masses = self.chemical_system.atom_property("atomic_weight")
        except KeyError:
            masses = np.array(
                [
                    ATOMS_DATABASE.get_atom_property(at, "atomic_weight")
                    for at in self.chemical_system.atom_list
                ],
            )
        masses = [masses[index] for index in atom_indices]
        grp = self._h5_file["/configuration"]

        coords = grp["coordinates"][first:last:step, atom_indices, :].astype(np.float64)

        if coords.ndim == 2:
            coords = coords[np.newaxis, :, :]

        if self._unit_cells is not None:
            direct_cells = np.array(
                [uc.direct for uc in self._unit_cells[first:last:step]],
            )
            inverse_cells = np.array(
                [uc.inverse for uc in self._unit_cells[first:last:step]],
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
                ],
            )

            com_traj = atomic_trajectory(com_coords, direct_cells, inverse_cells)

        else:
            com_traj = np.sum(
                coords[:, atom_indices, :] * masses[np.newaxis, :, np.newaxis],
                axis=1,
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
        if self._unit_cells is not None:
            real_coordinates = np.empty(box_coordinates.shape, dtype=np.float64)
            comp = 0
            for i in range(first, last, step):
                direct_cell = self._unit_cells[i].direct
                real_coordinates[comp, :] = box_coordinates[comp, :] @ direct_cell
                comp += 1
            return real_coordinates
        return box_coordinates

    def read_atomic_trajectory(
        self,
        index,
        first=0,
        last=None,
        step=1,
        *,
        box_coordinates=False,
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

        grp = self._h5_file["/configuration"]
        coords = grp["coordinates"][first:last:step, index, :].astype(np.float64)

        if self._unit_cells is not None:
            direct_cells = np.array(
                [self._unit_cells[nf].direct for nf in range(first, last, step)],
            )
            inverse_cells = np.array(
                [self._unit_cells[nf].inverse for nf in range(first, last, step)],
            )
            return atomic_trajectory(
                coords,
                direct_cells,
                inverse_cells,
                box_coordinates,
            )
        return coords

    def read_configuration_trajectory(
        self,
        index,
        first=0,
        last=None,
        step=1,
        variable="velocities",
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

        if not self.has_variable(variable):
            raise KeyError(f"The variable {variable} is not stored in the trajectory")

        grp = self._h5_file["/configuration"]
        return grp[variable][first:last:step, index, :].astype(np.float64)

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
        self, symbol: str, property_name: str
    ) -> Union[float, int, str]:
        """Get the value of a property for an atom type.

        If the trajectory's built-in atom database does not have
        the right atom, the function will fall back on the
        global atom database.

        Parameters
        ----------
        symbol : str
            Atom type label
        property_name : str
            Name of the atom property

        Returns
        -------
        Union[float, int, str]
            The value from the database converted to its type

        Raises
        ------
        KeyError
            The property name is not in the trajectory's database

        """
        if not self._has_database:
            return ATOMS_DATABASE.get_atom_property(symbol, property_name)
        if symbol not in self._has_atoms:
            if symbol in self._h5_file["/atom_database"]:
                self._has_atoms.append(symbol)
            else:
                return ATOMS_DATABASE.get_atom_property(symbol, property_name)
        if property_name not in self._property_map:
            temp = np.where(
                self._h5_file["/atom_database/property_labels"][:]
                == property_name.encode("utf-8"),
            )[0]
            if len(temp) == 0:
                if property_name == "dummy":
                    try:
                        return ATOMS_DATABASE.get_atom_property(symbol, property_name)
                    except KeyError:
                        if (
                            "_" in symbol
                        ):  # this is most likely an artificial atom from a molecule
                            return 0  # the molecule atoms are not dummy
                else:
                    raise KeyError(
                        f"Property {property_name} is not in the trajectory's internal database."
                    )
            index = temp.flatten()[0]
            self._property_map[property_name] = index
        index = self._property_map[property_name]
        if index not in self._data_types:
            self._data_types[index] = self._h5_file["/atom_database/property_types"][
                index
            ]
        data_type = self._data_types[index]
        if (symbol, index) not in self._property_cache:
            value = self._h5_file[f"/atom_database/{symbol}"][index]
            if data_type != b"complex":
                value = value.real
            self._property_cache[(symbol, index)] = value
        value = self._property_cache[(symbol, index)]
        if property_name == "color":
            value = float(value)
            num1 = round(value // 0x10000)
            num2 = round((value - num1 * 0x10000) // 0x100)
            num3 = round(value - num1 * 0x10000 - num2 * 0x100)
            return ";".join([str(int(x)) for x in [num1, num2, num3]])
        if data_type == b"int":
            return int(value)
        if data_type == b"str":
            if isinstance(value, bytes):
                return value.decode("utf-8")
            return value
        return float(value)

    def atoms_in_database(self) -> list[str]:
        """Return the list of all the atom types in the database.

        This list should match the list of unique atom types in the
        ChemicalSystem of this trajectory.

        Returns
        -------
        list[str]
            All the atom types saved in the trajectory's database

        """
        if "atom_database" not in self._h5_file:
            return ATOMS_DATABASE.atoms
        return list(self._h5_file["/atom_database"].keys())

    def properties_in_database(self) -> list[str]:
        """Return all the atom properties saved in the trajectory's database.

        Returns
        -------
        list[str]
            All the properties saved in the trajectory's database

        """
        if "atom_database" not in self._h5_file:
            return ATOMS_DATABASE.properties
        return [
            label.decode("utf-8")
            for label in self._h5_file["/atom_database/property_labels"]
        ]

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
    def file(self):
        """Return the trajectory file object.

        :return: the trajectory file object
        :rtype: HDF5 file object
        """
        return self._h5_file

    @property
    def filename(self):
        """Return the trajectory filename.

        :return: the trajectory filename
        :rtype: str
        """
        return self._h5_filename

    def variable(self, name: str):
        """Return a specific dataset corresponding to a variable called 'name'."""
        return self._h5_file["/configuration/" + name]

    def variables(self):
        """Return the configuration variables stored in this trajectory.

        :return; the configuration variable
        :rtype: list
        """
        grp = self._h5_file["/configuration"]

        return list(grp.keys())
