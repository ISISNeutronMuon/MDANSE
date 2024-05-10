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

from ast import operator
import os
from typing import Collection

import numpy as np
from icecream import ic
import h5py

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem, _ChemicalEntity
from MDANSE.Extensions import atomic_trajectory, com_trajectory, fold_coordinates
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import (
    build_connectivity,
    resolve_undefined_molecules_name,
    sorted_atoms,
)
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class MdanseTrajectory:
    """This used to be Trajectory, but has now been renamed.
    Trajectory is now a wrapper object, and MdanseTrajectory
    is the original implementation of the Mdanse HDF5 format.
    """

    def __init__(self, h5_filename):
        """Constructor.

        :param h5_filename: the trajectory filename
        :type h5_filename: str
        """

        ic("Trajectory.__init__ started")
        self._h5_filename = h5_filename

        self._h5_file = h5py.File(self._h5_filename, "r")

        ic("Trajectory.__init__ h5py.File created")
        # Load the chemical system
        self._chemical_system = ChemicalSystem(
            os.path.splitext(os.path.basename(self._h5_filename))[0]
        )
        self._chemical_system.load(self._h5_filename)

        ic("Trajectory.__init__ created ChemicalSystem")
        # Load all the unit cells
        self._load_unit_cells()

        ic("Trajectory.__init__ loaded unit cells")
        # Load the first configuration
        coords = self._h5_file["/configuration/coordinates"][0, :, :]
        if self._unit_cells:
            unit_cell = self._unit_cells[0]
            conf = PeriodicRealConfiguration(self._chemical_system, coords, unit_cell)
        else:
            conf = RealConfiguration(self._chemical_system, coords)
        self._chemical_system.configuration = conf

        ic("Trajectory.__init__ read coordinates")
        # Define a default name for all chemical entities which have no name
        resolve_undefined_molecules_name(self._chemical_system)

        ic("Trajectory.__init__ ended")

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

        grp = self._h5_file["/configuration"]
        configuration = {}
        for k, v in grp.items():
            configuration[k] = v[frame].astype(np.float64)

        for k in self._h5_file.keys():
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

    def coordinates(self, frame):
        """Return the coordinates at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the coordinates
        :rtype: ndarray
        """

        if frame < 0 or frame >= len(self):
            raise IndexError(f"Invalid frame number: {frame}")

        grp = self._h5_file["/configuration"]

        return grp["coordinates"][frame].astype(np.float64)

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
            unit_cell = self._unit_cells[frame]
        else:
            unit_cell = None

        variables = {}
        for k, v in self._h5_file["configuration"].items():
            variables[k] = v[frame, :, :].astype(np.float64)

        coordinates = variables.pop("coordinates")

        if unit_cell is None:
            conf = RealConfiguration(self._chemical_system, coordinates, **variables)
        else:
            conf = PeriodicRealConfiguration(
                self._chemical_system, coordinates, unit_cell, **variables
            )

        return conf

    def _load_unit_cells(self):
        """Load all the unit cells."""
        ic("_load_unit_cells")
        if "unit_cell" in self._h5_file:
            ic("_load_unit_cells: unit_cell IS in self._h5_file")
            self._unit_cells = [UnitCell(uc) for uc in self._h5_file["unit_cell"][:]]
            ic("_load_unit_cells: got unit_cell from self._h5_file")
        else:
            ic("_load_unit_cells: unit_cell IS NOT in self._h5_file")
            self._unit_cells = None
        ic("_load_unit_cells finished")

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
        else:
            return None

    def __len__(self):
        """Returns the length of the trajectory.

        :return: the number of frames of the trajectory
        :rtype: int
        """

        grp = self._h5_file["/configuration"]

        return grp["coordinates"].shape[0]

    def read_com_trajectory(
        self, atoms, first=0, last=None, step=1, box_coordinates=False
    ):
        """Build the trajectory of the center of mass of a set of atoms.

        :param atoms: the atoms for which the center of mass should be computed
        :type atoms: list MDANSE.Chemistry.ChemicalEntity.Atom
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

        indexes = [at.index for at in atoms]
        masses = np.array(
            [
                ATOMS_DATABASE.get_atom_property(at.symbol, "atomic_weight")
                for at in atoms
            ]
        )
        grp = self._h5_file["/configuration"]

        coords = grp["coordinates"][first:last:step, :, :].astype(np.float64)

        if coords.ndim == 2:
            coords = coords[np.newaxis, :, :]

        if self._unit_cells is not None:
            direct_cells = np.array([uc.transposed_direct for uc in self._unit_cells])
            inverse_cells = np.array([uc.transposed_inverse for uc in self._unit_cells])

            top_lvl_chemical_entities = set(
                [at.top_level_chemical_entity for at in atoms]
            )
            top_lvl_chemical_entities_indexes = [
                [at.index for at in e.atom_list] for e in top_lvl_chemical_entities
            ]
            bonds = {}
            for e in top_lvl_chemical_entities:
                for at in e.atom_list:
                    bonds[at.index] = [other_at.index for other_at in at.bonds]

            com_traj = com_trajectory.com_trajectory(
                coords,
                direct_cells,
                inverse_cells,
                masses,
                top_lvl_chemical_entities_indexes,
                indexes,
                bonds,
                box_coordinates=box_coordinates,
            )

        else:
            com_traj = np.sum(
                coords[:, indexes, :] * masses[np.newaxis, :, np.newaxis], axis=1
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
                direct_cell = self._unit_cells[i].transposed_direct
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

        grp = self._h5_file["/configuration"]
        coords = grp["coordinates"][first:last:step, index, :].astype(np.float64)

        if self._unit_cells is not None:
            direct_cells = np.array([uc.transposed_direct for uc in self._unit_cells])
            inverse_cells = np.array([uc.transposed_inverse for uc in self._unit_cells])
            atomic_traj = atomic_trajectory.atomic_trajectory(
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

        grp = self._h5_file["/configuration"]
        variable = grp[variable][first:last:step, index, :].astype(np.float64)

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
        if variable in self._h5_file["/configuration"]:
            return True
        else:
            return False

    @property
    def chemical_system(self):
        """Return the chemical system stored in the trajectory.

        :return: the chemical system
        :rtype: MDANSE.Chemistry.ChemicalEntity.ChemicalSystem
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

    def variables(self):
        """Return the configuration variables stored in this trajectory.

        :return; the configuration variable
        :rtype: list
        """

        grp = self._h5_file["/configuration"]

        return list(grp.keys())
