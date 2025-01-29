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
from typing import Union, List

import numpy as np
import h5py

from MDANSE.MLogging import LOG
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
    contiguous_coordinates_real,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import (
    atomic_trajectory,
)
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class H5MDTrajectory:
    """This is used by Trajectory, which is now a wrapper object.
    The H5MDTrajectory for now has been prepared to read the
    H5MD files created by MDMC.
    """

    def __init__(self, h5_filename: Union[Path, str]):
        """Constructor.

        :param h5_filename: the trajectory filename
        :type h5_filename: str
        """

        self._h5_filename = Path(h5_filename)

        self._h5_file = h5py.File(self._h5_filename, "r")

        # Load the chemical system
        try:
            chemical_elements = [
                byte.decode() for byte in self._h5_file["/parameters/atom_symbols"]
            ]
        except KeyError:
            chemical_elements = self._h5_file["/particles/all/species"]
        self._chemical_system = ChemicalSystem(self._h5_filename.stem)
        self._chemical_system.initialise_atoms(chemical_elements)

        # Load all the unit cells
        self._load_unit_cells()

        # Load the first configuration
        coords = self._h5_file["/particles/all/position/value"][0, :, :]
        try:
            pos_unit = self._h5_file["/particles/all/position/value"].attrs["unit"]
        except:
            conv_factor = 1.0
        else:
            if pos_unit == "Ang":
                pos_unit = "ang"
            conv_factor = measure(1.0, pos_unit).toval("nm")
        coords *= conv_factor

        self._variables_to_skip = []

    @classmethod
    def file_is_right(self, filename):
        result = True
        try:
            temp = h5py.File(filename)
        except FileNotFoundError:
            result = False
        else:
            try:
                temp["h5md"]
            except KeyError:
                result = False
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
            pos_unit = self._h5_file["/particles/all/position/value"].attrs["unit"]
        except:
            conv_factor = 1.0
        else:
            if pos_unit == "Ang":
                pos_unit = "ang"
            conv_factor = measure(1.0, pos_unit).toval("nm")
        configuration = {}
        configuration["coordinates"] = (
            self._h5_file["/particles/all/position/value"][frame, :, :] * conv_factor
        )
        try:
            try:
                vel_unit = self._h5_file["/particles/all/velocity/value"].attrs["unit"]
            except:
                vel_unit = "ang/fs"
            configuration["velocities"] = self._h5_file[
                "/particles/all/velocity/value"
            ][frame, :, :] * measure(1.0, vel_unit).toval("nm/ps")
        except:
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
        except:
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
        except:
            conv_factor = 1.0
        else:
            if pos_unit == "Ang":
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

        if self._unit_cells is not None:
            unit_cell = self.unit_cell(frame)
        else:
            unit_cell = None

        variables = {}
        for k in self.variables():
            if k not in self._variables_to_skip:
                try:
                    variables[k] = self.variable(k)[frame, :, :].astype(np.float64)
                except:
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
        except:
            conv_factor = 1.0
        else:
            if box_unit == "Ang":
                box_unit = "ang"
            conv_factor = measure(1.0, box_unit).toval("nm")
        try:
            cells = self._h5_file["/particles/all/box/edges/value"][:] * conv_factor
        except KeyError:
            self._unit_cells = None
        else:
            if len(cells.shape) > 1:
                for cell in cells:
                    temp_array = np.array(
                        [[cell[0], 0.0, 0.0], [0.0, cell[1], 0.0], [0.0, 0.0, cell[2]]]
                    )
                    uc = UnitCell(temp_array)
                    self._unit_cells.append(uc)
            else:
                temp_array = np.array(
                    [[cells[0], 0.0, 0.0], [0.0, cells[1], 0.0], [0.0, 0.0, cells[2]]]
                )
                self._unit_cells.append(UnitCell(temp_array))

    def time(self):
        try:
            time_unit = self._h5_file["/particles/all/position/time"].attrs["unit"]
        except:
            conv_factor = 1.0
        else:
            conv_factor = measure(1.0, time_unit).toval("ps")
        try:
            time = self._h5_file["/particles/all/position/time"] * conv_factor
        except:
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
        except:
            conv_factor = 1.0
        else:
            if pos_unit == "Ang":
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
                direct_cell = self.unit_cell(i).transposed_direct
                real_coordinates[comp, :] = np.matmul(
                    direct_cell, box_coordinates[comp, :]
                )
                comp += 1
            return real_coordinates
        else:
            return box_coordinates

    def read_atomic_trajectory(
        self, index, first=0, last=None, step=1, box_coordinates=False
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

        grp = self._h5_file["/particles/all/position/value"]
        try:
            pos_unit = self._h5_file["/particles/all/position/value"].attrs["unit"]
        except:
            conv_factor = 1.0
        else:
            if pos_unit == "Ang":
                pos_unit = "ang"
            conv_factor = measure(1.0, pos_unit).toval("nm")
        coords = grp[first:last:step, index, :].astype(np.float64) * conv_factor

        if self._unit_cells is not None:
            direct_cells = np.array(
                [
                    self.unit_cell(nf).transposed_direct
                    for nf in range(first, last, step)
                ]
            )
            inverse_cells = np.array(
                [
                    self.unit_cell(nf).transposed_inverse
                    for nf in range(first, last, step)
                ]
            )
            atomic_traj = atomic_trajectory(
                coords, direct_cells, inverse_cells, box_coordinates
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

        if not self.has_variable(variable):
            raise KeyError(
                "The variable {} is not stored in the trajectory".format(variable)
            )

        grp = self._h5_file["/particles/all"]
        variable = grp[variable]["value"][first:last:step, index, :].astype(np.float64)

        return variable

    def has_variable(self, variable: str) -> bool:
        """Check if the trajectory has a specific variable e.g.
        velocities.

        Parameters
        ----------
        variable : str
            The variable to check the existence of.

        Returns
        -------
        bool
            True if variable exists.
        """
        if variable in self._h5_file["/particles/all"]:
            return True
        else:
            return False

    def get_atom_property(self, atom_symbol: str, property: str):
        return ATOMS_DATABASE.get_atom_property(atom_symbol, property)

    def atoms_in_database(self) -> List[str]:
        return ATOMS_DATABASE.atoms

    def properties_in_database(self) -> List[str]:
        return ATOMS_DATABASE.properties

    @property
    def chemical_system(self):
        """Return the chemical system stored in the trajectory.

        :return: the chemical system
        :rtype: MDANSE.Chemistry.ChemicalSystem.ChemicalSystem
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
        """Returns a specific dataset corresponding
        to a trajectory variable called 'name'.
        """

        try:
            grp = self._h5_file["/particles/all/" + name + "/value"]
        except KeyError:
            grp = self._h5_file["/particles/all/" + name]

        return grp

    def variables(self):
        """Return the configuration variables stored in this trajectory.

        :return; the configuration variable
        :rtype: list
        """

        grp = self._h5_file["/particles/all"]

        return list(grp.keys())
