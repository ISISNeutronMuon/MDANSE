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


class TrajectoryError(Exception):
    pass


class Trajectory:
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
            raise TrajectoryError(f"Invalid frame number: {frame}")

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
            raise TrajectoryError(f"Invalid frame number: {frame}")

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
            raise TrajectoryError(f"Invalid frame number: {frame}")

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
            raise TrajectoryError(
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
            return False
        else:
            return True

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


class TrajectoryWriterError(Exception):
    pass


class TrajectoryWriter:
    allowed_compression = ["gzip", "lzf"]

    def __init__(
        self,
        h5_filename,
        chemical_system: ChemicalSystem,
        n_steps,
        selected_atoms=None,
        positions_dtype=np.float64,
        chunking_axis=1,
        compression="none",
    ):
        """Constructor.

        :param h5_filename: the trajectory filename
        :type h5_filename: str
        :param chemical_system: the chemical system
        :type h5_filename: MDANSE.Chemistry.ChemicalEntity.ChemicalSystem
        :param h5_filename: the number of steps
        :type h5_filename: int
        :param selected_atoms: the selected atoms of the chemical system to write
        :type selected_atoms: list of MDANSE.Chemistry.ChemicalEntity.Atom
        """

        self._h5_filename = h5_filename

        self._h5_file = h5py.File(self._h5_filename, "w")

        self._chemical_system = chemical_system

        if selected_atoms is None:
            self._selected_atoms = self._chemical_system.atom_list
        else:
            for at in selected_atoms:
                if at.root_chemical_system != chemical_system:
                    raise TrajectoryWriterError(
                        "One or more atoms of the selection comes from a different chemical system"
                    )
            self._selected_atoms = sorted_atoms(selected_atoms)

        self._selected_atoms = [at.index for at in self._selected_atoms]

        all_atoms = self._chemical_system.atom_list
        for idx in self._selected_atoms:
            all_atoms[idx] = False

        self._dump_chemical_system()

        self._h5_file.create_group("/configuration")

        self._n_steps = n_steps

        self._current_index = 0

        self._dtype = positions_dtype

        self._chunking_axis = chunking_axis

        self._compression = compression

    def _dump_chemical_system(self):
        """Dump the chemical system to the trajectory file."""

        self._chemical_system.serialize(self._h5_file)

    @property
    def chemical_system(self):
        return self._chemical_system

    def close(self):
        """Close the trajectory file"""

        self._h5_file.close()

    def dump_configuration(self, time, units=None):
        """Dump the chemical system configuration at a given time.

        :param time: the time
        :type time: float

        :param units: the units
        :type units: dict
        """

        if self._current_index >= self._n_steps:
            raise TrajectoryError(
                f"The current index {self._current_index} is greater than the actual number of steps of the trajectory {self._n_steps}"
            )

        configuration = self._chemical_system.configuration
        if configuration is None:
            return

        if units is None:
            units = {}

        n_atoms = self._chemical_system.total_number_of_atoms

        if self._chunking_axis == 1:
            chunk_tuple = (1, n_atoms, 3)
        else:
            chunk_tuple = (self._n_steps, 1, 3)

        # Write the configuration variables
        configuration_grp = self._h5_file["/configuration"]
        for k, v in configuration.variables.items():
            data = np.empty(v.shape)
            data[:] = np.nan
            data[self._selected_atoms, :] = v[self._selected_atoms, :]
            dset = configuration_grp.get(k, None)
            if dset is None:
                if self._compression in TrajectoryWriter.allowed_compression:
                    dset = configuration_grp.create_dataset(
                        k,
                        shape=(self._n_steps, n_atoms, 3),
                        chunks=(1, n_atoms, 3),
                        dtype=self._dtype,
                        compression=self._compression,
                    )
                else:
                    dset = configuration_grp.create_dataset(
                        k,
                        shape=(self._n_steps, n_atoms, 3),
                        chunks=(1, n_atoms, 3),
                        dtype=self._dtype,
                    )
                dset.attrs["units"] = units.get(k, "")
            dset[self._current_index] = data

        # Write the unit cell
        if configuration.is_periodic:
            unit_cell = configuration.unit_cell
            unit_cell_dset = self._h5_file.get("unit_cell", None)
            if unit_cell_dset is None:
                unit_cell_dset = self._h5_file.create_dataset(
                    "unit_cell",
                    shape=(self._n_steps, 3, 3),
                    chunks=(1, 3, 3),
                    dtype=np.float64,
                )
                unit_cell_dset.attrs["units"] = units.get("unit_cell", "")
            unit_cell_dset[self._current_index] = unit_cell.direct

        # Write the time
        time_dset = self._h5_file.get("time", None)
        if time_dset is None:
            time_dset = self._h5_file.create_dataset(
                "time", shape=(self._n_steps,), dtype=np.float64
            )
            time_dset.attrs["units"] = units.get("time", "")
        time_dset[self._current_index] = time

        self._current_index += 1


class RigidBodyTrajectoryGenerator:
    """Compute the Rigid-body trajectory data

    If rbt is a RigidBodyTrajectory object, then

     * len(rbt) is the number of steps stored in it
     * rbt[i] is the value at step i (a vector for the center of mass
       and a quaternion for the orientation)
    """

    def __init__(
        self,
        trajectory,
        chemical_entity: _ChemicalEntity,
        reference,
        first=0,
        last=None,
        step=1,
    ):
        """Constructor.

        :param trajectory: the input trajectory
        :type trajectory: MDANSE.Trajectory.Trajectory
        :param chemical_entity: the chemical enitty for which the Rigig-Body trajectory should be computed
        :type chemical_entity: MDANSE.Chemistry.ChemicalEntity.ChemicalEntity
        :param reference: the reference configuration. Must be continuous.
        :type reference: MDANSE.MolecularDynamics.Configuration.Configuration
        :param first: the index of the first frame
        :type first: int
        :param last: the index of the last frame
        :type last: int
        :param step: the step in frame
        :type step: int
        """

        self._trajectory = trajectory

        if last is None:
            last = len(self._trajectory)

        atoms = chemical_entity.atom_list

        masses = [
            ATOMS_DATABASE.get_atom_property(at.symbol, "atomic_weight") for at in atoms
        ]

        mass = sum(masses)

        ref_com = chemical_entity.center_of_mass(reference)

        n_steps = len(range(first, last, step))

        possq = np.zeros((n_steps,), np.float64)
        cross = np.zeros((n_steps, 3, 3), np.float64)

        rcms = self._trajectory.read_com_trajectory(
            atoms, first, last, step, box_coordinates=True
        )

        # relative coords of the CONTIGUOUS reference
        r_ref = np.zeros((len(atoms), 3), np.float64)
        for i, at in enumerate(atoms):
            r_ref[i] = reference["coordinates"][at.index, :] - ref_com

        unit_cells, inverse_unit_cells = self._trajectory.get_unit_cells()
        if unit_cells is not None:
            unit_cells = unit_cells[first:last:step, :, :]
            inverse_unit_cells = inverse_unit_cells[first:last:step, :, :]

        for i, at in enumerate(atoms):
            r = self._trajectory.read_atomic_trajectory(
                at.index, first, last, step, True
            )
            r = r - rcms

            r = r[:, np.newaxis, :]
            r = fold_coordinates.fold_coordinates(
                r, unit_cells, inverse_unit_cells, True
            )
            r = np.squeeze(r)

            r = self._trajectory.to_real_coordinates(r, first, last, step)
            w = masses[i] / mass
            np.add(possq, w * np.add.reduce(r * r, -1), possq)
            np.add(possq, w * np.add.reduce(r_ref[i] * r_ref[i], -1), possq)
            np.add(cross, w * r[:, :, np.newaxis] * r_ref[np.newaxis, i, :], cross)

        rcms = self._trajectory.to_real_coordinates(rcms, first, last, step)

        # filling matrix M
        k = np.zeros((n_steps, 4, 4), np.float64)
        k[:, 0, 0] = -cross[:, 0, 0] - cross[:, 1, 1] - cross[:, 2, 2]
        k[:, 0, 1] = cross[:, 1, 2] - cross[:, 2, 1]
        k[:, 0, 2] = cross[:, 2, 0] - cross[:, 0, 2]
        k[:, 0, 3] = cross[:, 0, 1] - cross[:, 1, 0]
        k[:, 1, 1] = -cross[:, 0, 0] + cross[:, 1, 1] + cross[:, 2, 2]
        k[:, 1, 2] = -cross[:, 0, 1] - cross[:, 1, 0]
        k[:, 1, 3] = -cross[:, 0, 2] - cross[:, 2, 0]
        k[:, 2, 2] = cross[:, 0, 0] - cross[:, 1, 1] + cross[:, 2, 2]
        k[:, 2, 3] = -cross[:, 1, 2] - cross[:, 2, 1]
        k[:, 3, 3] = cross[:, 0, 0] + cross[:, 1, 1] - cross[:, 2, 2]

        for i in range(1, 4):
            for j in range(i):
                k[:, i, j] = k[:, j, i]
        np.multiply(k, 2.0, k)
        for i in range(4):
            np.add(k[:, i, i], possq, k[:, i, i])

        quaternions = np.zeros((n_steps, 4), np.float64)
        fit = np.zeros((n_steps,), np.float64)
        for i in range(n_steps):
            e, v = np.linalg.eig(k[i])
            v = np.transpose(v)
            j = np.argmin(e)
            if e[j] < 0.0:
                fit[i] = 0.0
            else:
                fit[i] = np.sqrt(e[j])
            if v[j, 0] < 0.0:
                quaternions[i] = -v[j]
            else:
                quaternions[i] = v[j]

        self.fit = fit
        self.cms = rcms
        self.quaternions = quaternions

    def __len__(self):
        return self.cms.shape[0]

    def __getitem__(self, index):
        from MDANSE.Mathematics.Geometry import Vector
        from MDANSE.Mathematics.LinearAlgebra import Quaternion

        return Vector(self.cms[index]), Quaternion(self.quaternions[index])


def partition_universe(universe, groups):
    atoms = sorted(universe.atomList(), key=operator.attrgetter("index"))

    coll = [Collection([atoms[index] for index in gr]) for gr in groups]

    return coll


def read_atoms_trajectory(
    trajectory,
    atoms,
    first,
    last=None,
    step=1,
    variable="configuration",
    weights=None,
    dtype=np.float64,
):
    if not isinstance(atoms, (list, tuple)):
        atoms = [atoms]

    if last is None:
        last = len(trajectory)

    nFrames = len(list(range(first, last, step)))

    serie = np.zeros((nFrames, 3), dtype=dtype)

    if weights is None or len(atoms) == 1:
        weights = [1.0] * len(atoms)

    # cs.configuration = conf

    # tw = TrajectoryWriter('toto.h5',cs)
    # tw.dump_configuration()
    # tw.close()

    # t = Trajectory('toto.h5')
    # print(t.read_atom_trajectory(2))
    # t.close()

    # import numpy as np

    # from MDANSE.MolecularDynamics.Configuration import RealConfiguration

    # from MDANSE.Chemistry.ChemicalEntity import Atom
    # cs = ChemicalSystem()
    # for i in range(768):
    #     cs.add_chemical_entity(Atom(symbol='H'))

    # coords = np.load('coords.npy')
    # unit_cell = np.load('unit_cell.npy')

    # tw = TrajectoryWriter('waterbox.h5',cs)

    # n_frames = coords.shape[0]
    # for i in range(n_frames):
    #     c = RealConfiguration(cs,coords[i,:,:],unit_cell[i,:,:])
    #     cs.configuration = c
    #     tw.dump_configuration()

    # tw.close()

    # t = Trajectory('waterbox.h5')
    # t.close()


if __name__ == "__main__":
    from MDANSE.MolecularDynamics.Configuration import RealConfiguration

    from MDANSE.Chemistry.ChemicalEntity import Atom

    cs = ChemicalSystem()
    for i in range(2):
        cs.add_chemical_entity(Atom(symbol="H"))

    tw = TrajectoryWriter("test.h5", cs)
    unit_cell = 10.0 * np.identity(3)

    coords = np.empty((2, 3), dtype=np.float64)
    coords[0, :] = [-4, 0, 0]
    coords[1, :] = [4, 0, 0]

    c = RealConfiguration(cs, coords, unit_cell)
    cs.configuration = c
    tw.dump_configuration(1.0)
    tw.close()

    t = Trajectory("test.h5")
    print(t.read_cog_trajectory([0, 1], 0, 10, 1).shape)
    t.close()
