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

from pathlib import Path

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
from MDANSE.MolecularDynamics.UnitCell import (
    BAD_CELL,
    CELL_SIZE_LIMIT,
    CHANGING_CELL,
    NO_CELL,
    UnitCell,
)


class H5MDTrajectory:
    """This is used by Trajectory, which is now a wrapper object.
    The H5MDTrajectory for now has been prepared to read the
    H5MD files created by MDMC.
    """

    def __init__(self, h5_filename: Path | str):
        """Constructor.

        :param h5_filename: the trajectory filename
        :type h5_filename: str
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
            else:
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

        # Load all the unit cells
        self._load_unit_cells()

        # Load the first configuration
        coords = self._h5_file["/particles/all/position/value"][0, :, :]
        try:
            pos_unit = self._h5_file["/particles/all/position/value"].attrs["unit"]
        except KeyError:
            conv_factor = 1.0
        else:
            if pos_unit in ("Ang", "Angstrom"):
                pos_unit = "ang"
            conv_factor = measure(1.0, pos_unit).toval("nm")
        coords *= conv_factor

        self._variables_to_skip = []

    @classmethod
    def file_is_right(self, filename):
        result = True
        try:
            temp = h5py.File(filename)
        except Exception:
            result = False
        else:
            try:
                temp["h5md"]
            except Exception:
                result = False
            temp.close()
        return result

    def close(self):
        """Close the trajectory."""

        self._h5_file.close()

    def __getitem__(self, frame):
        """Return the configuration at a given frame

        :param frame: the frame
        :type frame: int

        :return: the configuration
        :rtype: dict of ndarray
        """

        grp = self._h5_file["/particles/all/position/value"]
        try:
            pos_unit = grp.attrs["unit"]
        except Exception:
            conv_factor = 1.0
        else:
            if pos_unit in ("Ang", "Angstrom"):
                pos_unit = "ang"
            conv_factor = measure(1.0, pos_unit).toval("nm")
        configuration = {}
        configuration["coordinates"] = grp[frame, :, :] * conv_factor
        try:
            try:
                vel_unit = self._h5_file["/particles/all/velocity/value"].attrs["unit"]
            except Exception:
                vel_unit = "ang/fs"
            configuration["velocities"] = self._h5_file[
                "/particles/all/velocity/value"
            ][frame, :, :] * measure(1.0, vel_unit).toval("nm/ps")
        except Exception:
            pass

        configuration["time"] = self.time()[frame]
        try:
            configuration["unit_cell"] = self._unit_cells[frame]
        except IndexError:
            configuration["unit_cell"] = self._unit_cells[0]

        return configuration

    def __getstate__(self):
        d = self.__dict__.copy()
        del d["_h5_file"]
        return d

    def __setstate__(self, state):
        self.__dict__ = state
        self._h5_file = h5py.File(state["_h5_filename"], "r")

    def charges(self, frame):
        """Return the electrical charge of atoms at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the coordinates
        :rtype: ndarray
        """

        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")
        try:
            charge = self._h5_file["/particles/all/charge/value"][frame]
        except KeyError:
            LOG.debug(f"No charge information in trajectory {self._h5_filename}")
            charge = np.zeros(self._chemical_system.number_of_atoms)
        except Exception:
            try:
                charge = self._h5_file["/particles/all/charge"][:]
            except KeyError:
                LOG.debug(f"No charge information in trajectory {self._h5_filename}")
                charge = np.zeros(self._chemical_system.number_of_atoms)

        return charge.astype(np.float64)

    def coordinates(self, frame):
        """Return the coordinates at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the coordinates
        :rtype: ndarray
        """

        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")
        try:
            pos_unit = self._h5_file["/particles/all/position/value"].attrs["unit"]
        except Exception:
            conv_factor = 1.0
        else:
            if pos_unit in ("Ang", "Angstrom"):
                pos_unit = "ang"
            conv_factor = measure(1.0, pos_unit).toval("nm")

        retval = self._h5_file["/particles/all/position/value"][frame, :, :]

        return retval.astype(np.float64) * conv_factor

    def configuration(self, frame):
        """Build and return a configuration at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the configuration
        :rtype: MDANSE.MolecularDynamics.Configuration.Configuration
        """

        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        unit_cell = self.unit_cell(frame) if self._unit_cells is not None else None

        variables = {}
        for k in self.variables():
            if k not in self._variables_to_skip:
                try:
                    variables[k] = self.variable(k)[frame, :, :].astype(np.float64)
                except Exception:
                    self._variables_to_skip.append(k)

        coordinates = self.coordinates(frame)

        if unit_cell is None:
            conf = RealConfiguration(self._chemical_system, coordinates, **variables)
        else:
            conf = PeriodicRealConfiguration(
                self._chemical_system, coordinates, unit_cell, **variables
            )

        return conf

    def _load_unit_cells(self):
        """Load all the unit cells."""
        self._unit_cells = []
        try:
            box_unit = self._h5_file["/particles/all/box/edges/value"].attrs["unit"]
        except (AttributeError, KeyError):
            conv_factor = 0.1
        else:
            if box_unit in ("Ang", "Angstrom"):
                box_unit = "ang"
            conv_factor = measure(1.0, box_unit).toval("nm")
        try:
            cells = self._h5_file["/particles/all/box/edges/value"][:] * conv_factor
        except KeyError:
            self._unit_cells = None
            self.unit_cell_warning = NO_CELL
        else:
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

    def time(self):
        try:
            time_unit = self._h5_file["/particles/all/position/time"].attrs["unit"]
        except KeyError:
            conv_factor = 1.0
        else:
            conv_factor = measure(1.0, time_unit).toval("ps")
        try:
            time = self._h5_file["/particles/all/position/time"] * conv_factor
        except TypeError:
            try:
                time = self._h5_file["/particles/all/position/time"][:] * conv_factor
            except Exception:
                time = []
        return time

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
            try:
                uc = self._unit_cells[frame]
            except IndexError:
                uc = self._unit_cells[0]
            return uc
        else:
            return None

    def __len__(self):
        """Returns the length of the trajectory.

        :return: the number of frames of the trajectory
        :rtype: int
        """

        grp = self._h5_file["/particles/all/position/value"]

        return grp.shape[0]

    def read_com_trajectory(
        self, atom_indices, first=0, last=None, step=1, box_coordinates=False
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

        atoms = self.chemical_system.atom_list

        try:
            masses = self._h5_file["/particles/all/mass/value"][atom_indices].astype(
                np.float64
            )
        except KeyError:
            try:
                masses = self._h5_file["/particles/all/mass"][atom_indices].astype(
                    np.float64
                )
            except KeyError:
                masses = np.array(
                    [
                        ATOMS_DATABASE.get_atom_property(at, "atomic_weight")
                        for at in atoms
                    ]
                )[atom_indices]
        grp = self._h5_file["/particles/all/position/value"]
        try:
            pos_unit = self._h5_file["/particles/all/position/value"].attrs["unit"]
        except Exception:
            conv_factor = 1.0
        else:
            if pos_unit in ("Ang", "Angstrom"):
                pos_unit = "ang"
            conv_factor = measure(1.0, pos_unit).toval("nm")

        coords = grp[first:last:step, atom_indices, :].astype(np.float64) * conv_factor

        if coords.ndim == 2:
            coords = coords[np.newaxis, :, :]

        if self._unit_cells is not None:
            direct_cells = np.array(
                [self.unit_cell(nf).direct for nf in range(first, last, step)]
            )
            inverse_cells = np.array(
                [self.unit_cell(nf).inverse for nf in range(first, last, step)]
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
                coords[:, atom_indices, :] * masses[np.newaxis, :, np.newaxis], axis=1
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
                direct_cell = self.unit_cell(i).direct
                real_coordinates[comp, :] = box_coordinates[comp, :] @ direct_cell
                comp += 1
            return real_coordinates
        return box_coordinates

    def read_atomic_trajectory(
        self,
        index: int,
        first: int = 0,
        last: int | None = None,
        step: int = 1,
        *,
        box_coordinates: bool = False,
    ) -> np.ndarray:
        """Read an atomic trajectory. The trajectory is corrected from box jumps.

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
        box_coordinates : bool, optional
            If True, return fractional coordinates, by default False

        Returns
        -------
        np.ndarray
            Coordinates of one atom for specified time frames.

        """
        if last is None:
            last = len(self)

        grp = self._h5_file["/particles/all/position/value"]
        try:
            pos_unit = self._h5_file["/particles/all/position/value"].attrs["unit"]
        except Exception:
            conv_factor = 1.0
        else:
            if pos_unit in ("Ang", "Angstrom"):
                pos_unit = "ang"
            conv_factor = measure(1.0, pos_unit).toval("nm")
        coords = grp[first:last:step, index, :].astype(np.float64) * conv_factor

        if self._unit_cells is not None:
            direct_cells = np.array(
                [self.unit_cell(nf).direct for nf in range(first, last, step)],
            )
            inverse_cells = np.array(
                [self.unit_cell(nf).inverse for nf in range(first, last, step)],
            )
            return atomic_trajectory(
                coords,
                direct_cells,
                inverse_cells,
                box_coordinates=box_coordinates,
            )
        return coords

    def read_configuration_trajectory(
        self,
        index: int,
        first: int = 0,
        last: int | None = None,
        step: int = 1,
        variable="velocities",
    ) -> np.ndarray:
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
        np.ndarray
            Value of 'variable' for one atom and selected frames.

        Raises
        ------
        KeyError
            If 'variable' is not in the trajectory file.

        """
        if last is None:
            last = len(self)

        if not self.has_variable(variable):
            raise KeyError(f"The variable {variable} is not stored in the trajectory")

        grp = self._h5_file["/particles/all"]
        return grp[variable]["value"][first:last:step, index, :].astype(np.float64)

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

    def properties_in_database(self) -> list[str]:
        """Return the list of atom properties provided by the trajectory.

        Here, it defaults to the central atom property database.

        Returns
        -------
        list[str]
            List of atom property names that can be accessed.

        """
        return ATOMS_DATABASE.properties

    @property
    def chemical_system(self) -> ChemicalSystem:
        """The ChemicalSystem built from the trajectory contents."""
        return self._chemical_system

    @property
    def file(self):
        """The file object of the trajectory."""
        return self._h5_file

    @property
    def filename(self):
        """The filename of the trajectory."""
        return self._h5_filename

    def variable(self, name: str) -> h5py.Dataset:
        """Return the dataset corresponding to a trajectory variable called 'name'."""
        try:
            grp = self._h5_file["/particles/all/" + name + "/value"]
        except KeyError:
            grp = self._h5_file["/particles/all/" + name]
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
