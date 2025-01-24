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
import operator
from typing import TYPE_CHECKING, Any, Collection, Dict, List, Union

if TYPE_CHECKING:
    from MDANSE.Chemistry.Databases import AtomsDatabase

import math
from pathlib import Path

import h5py
import numpy as np
from MDANSE import PLATFORM
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.Trajectory.H5MDTrajectory import H5MDTrajectory
from MDANSE.Trajectory.MdanseTrajectory import MdanseTrajectory

available_formats = {
    "MDANSE": MdanseTrajectory,
    "H5MD": H5MDTrajectory,
}


class Trajectory:
    """This is a wrapper class, allowing us to implement
    multiple trajectory formats, while keeping the API unchanged
    for the analysis code.
    """

    def __init__(self, filename, trajectory_format=None):
        self._filename = filename
        self._format = trajectory_format
        if self._format is None:
            self.guess_correct_format()
        self._trajectory = self.open_trajectory(self._format)
        self._min_span = np.zeros(3)
        self._max_span = np.zeros(3)
        self._atom_cache = {}

    def guess_correct_format(self):
        """This is a placeholder for now. As the number of
        formats increases, they will have to be handled here.
        """
        for fname, fclass in available_formats.items():
            if fclass.file_is_right(self._filename):
                self._format = fname

    def open_trajectory(self, trajectory_format):
        trajectory_class = available_formats[trajectory_format]
        trajectory = trajectory_class(self._filename)
        return trajectory

    def close(self):
        """Close the trajectory."""

        self._trajectory.close()

    def __getitem__(self, frame):
        """Return the configuration at a given frame

        :param frame: the frame
        :type frame: int

        :return: the configuration
        :rtype: dict of ndarray
        """
        return self._trajectory[frame]

    def __getstate__(self):
        d = self.__dict__.copy()
        del d["_trajectory"]
        return d

    def __setstate__(self, state):
        self.__dict__ = state
        self._trajectory = self.open_trajectory(self._format)

    def __len__(self):
        return len(self._trajectory)

    def charges(self, frame):
        """Return the coordinates at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the coordinates
        :rtype: ndarray
        """

        return self._trajectory.charges(frame)

    def coordinates(self, frame):
        """Return the coordinates at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the coordinates
        :rtype: ndarray
        """

        return self._trajectory.coordinates(frame)

    def configuration(self, frame: int = 0):
        """Build and return a configuration at a given frame.

        :param frame: the frame
        :type frame: int

        :return: the configuration
        :rtype: MDANSE.MolecularDynamics.Configuration.Configuration
        """

        return self._trajectory.configuration(frame)

    def _load_unit_cells(self):
        """Load all the unit cells."""
        self._trajectory._load_unit_cells()

    def time(self):
        return self._trajectory.time()

    def unit_cell(self, frame):
        """Return the unit cell at a given frame. If no unit cell is defined, returns None.

        :param frame: the frame number
        :type frame: int

        :return: the unit cell
        :rtype: ndarray
        """

        return self._trajectory.unit_cell(frame)

    def calculate_coordinate_span(self) -> None:
        min_span = np.array(3 * [1e11])
        max_span = np.zeros(3)
        for frame in range(len(self)):
            coords = self.coordinates(frame)
            span = coords.max(axis=0) - coords.min(axis=0)
            min_span = np.minimum(span, min_span)
            max_span = np.maximum(span, max_span)
        self._max_span = max_span
        self._min_span = min_span

    @property
    def max_span(self):
        if np.allclose(self._max_span, 0.0):
            self.calculate_coordinate_span()
        return self._max_span

    @property
    def min_span(self):
        if np.allclose(self._min_span, 0.0):
            self.calculate_coordinate_span()
        return self._min_span

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
        return self._trajectory.read_com_trajectory(
            atom_indices,
            first=first,
            last=last,
            step=step,
            box_coordinates=box_coordinates,
        )

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
        return self._trajectory.to_real_coordinates(box_coordinates, first, last, step)

    def read_atomic_trajectory(
        self, index, first=0, last=None, step=1, box_coordinates=False
    ):
        """Read an atomic trajectory. The trajectory is corrected for box jumps.

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

        return self._trajectory.read_atomic_trajectory(
            index, first=first, last=last, step=step, box_coordinates=box_coordinates
        )

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
        return self._trajectory.read_configuration_trajectory(
            index, first=first, last=last, step=step, variable=variable
        )

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
        return self._trajectory.has_variable(variable)

    def get_atom_property(self, atom_symbol: str, property: str):
        if (atom_symbol, property) not in self._atom_cache.keys():
            self._atom_cache[(atom_symbol, property)] = (
                self._trajectory.get_atom_property(atom_symbol, property)
            )
        return self._atom_cache[(atom_symbol, property)]

    def has_atom(self, symbol: str):
        return symbol in self.atoms_in_database

    def get_property_dict(self, symbol: str) -> Dict[str, Any]:
        """Returns a dictionary of all the properties of an atom type.

        Parameters
        ----------
        symbol : str
            Symbol of the atom.

        Returns
        -------
        Union[int, float, str]
            The atom property.
        """
        return {
            property_name: self.get_atom_property(symbol, property_name)
            for property_name in self.properties_in_database
        }

    @property
    def atoms_in_database(self) -> List[str]:
        return self._trajectory.atoms_in_database()

    @property
    def properties_in_database(self) -> List[str]:
        return self._trajectory.properties_in_database()

    @property
    def chemical_system(self):
        """Return the chemical system stored in the trajectory.

        :return: the chemical system
        :rtype: MDANSE.Chemistry.ChemicalSystem.ChemicalSystem
        """
        return self._trajectory.chemical_system

    @property
    def file(self):
        """Return the trajectory file object.

        :return: the trajectory file object
        :rtype: HDF5 file object
        """

        return self._trajectory.file

    @property
    def filename(self):
        """Return the trajectory filename.

        :return: the trajectory filename
        :rtype: str
        """

        return self._trajectory.filename

    def variable(self, name: str):
        """Return a variable stored in the trajectory
        under the key 'name'.
        """

        return self._trajectory.variable(name)

    def variables(self):
        """Return the configuration variables stored in this trajectory.

        :return; the configuration variable
        :rtype: list
        """

        return self._trajectory.variables()


additive_atom_properties = [
    "nucleon",
    "b_incoherent2",
    "xray_asf_b4",
    "proton",
    "atomic_weight",
    "ionization_energy",
    "xs_absorption",
    "xs_scattering",
    "b_incoherent",
    "b_coherent",
    "charge",
    "xray_asf_c",
    "neutron",
    "xray_asf_a4",
    "xray_asf_a2",
    "xray_asf_a3",
    "xray_asf_a1",
    "xray_asf_b3",
    "xray_asf_b2",
    "xray_asf_b1",
    "xs_incoherent",
    "xs_coherent",
    "nuclear_spin",
]
averaged_atom_properties = [
    "electronegativity",
    "electroaffinity",
    "atomic_number",
    "group",
    "serie",
]
constant_atom_properties = {
    "equal": 1.0,
    "abundance": 100.0,
}
atom_radii = [
    "covalent_radius",
    "vdw_radius",
    "atomic_radius",
]


def create_average_atom(
    atom_dictionary: Dict[str, int], database: Trajectory, radius_padding: float = 0.0
):
    all_properties = database.properties_in_database
    values = {}
    for property in all_properties:
        temp = []
        total = 0
        for element_name, element_count in atom_dictionary.items():
            temp.append(
                [database.get_atom_property(element_name, property), element_count]
            )
        if property in additive_atom_properties:
            total = np.sum([float(x[0]) * int(x[1]) for x in temp])
        elif property in averaged_atom_properties:
            total = np.sum([float(x[0]) * int(x[1]) for x in temp]) / np.sum(
                [int(x[1]) for x in temp]
            )
        elif property in constant_atom_properties.keys():
            total = constant_atom_properties[property]
        elif property in atom_radii:
            total = (
                np.sum([float(x[0]) * int(x[1]) for x in temp])
                / np.sum([int(x[1]) for x in temp])
                + radius_padding
            )
        else:
            for entry in temp:
                try:
                    converted = float(entry[0])
                except TypeError:
                    total = entry
                except ValueError:
                    total = entry
                else:
                    total += converted * entry[1]
        values[property] = total
    is_dummy = 1
    for element_name, _ in atom_dictionary.items():
        is_dummy = is_dummy and database.get_atom_property(element_name, "dummy")
    values["dummy"] = is_dummy
    return values


class TrajectoryWriterError(Exception):
    pass


class TrajectoryWriter:
    allowed_compression = ["gzip", "lzf"]

    def __init__(
        self,
        h5_filename: Union[Path, str],
        chemical_system: ChemicalSystem,
        n_steps,
        selected_atoms=None,
        positions_dtype=np.float64,
        chunking_limit=128,
        compression="none",
        initial_charges=None,
    ):
        """Constructor.

        :param h5_filename: the trajectory filename
        :type h5_filename: str
        :param chemical_system: the chemical system
        :type h5_filename: MDANSE.Chemistry.ChemicalSystem.ChemicalSystem
        :param h5_filename: the number of steps
        :type h5_filename: int
        :param selected_atoms: the selected atoms of the chemical system to write
        :type selected_atoms: list of MDANSE.Chemistry.ChemicalSystem.Atom
        """

        self._h5_filename = Path(h5_filename)
        PLATFORM.create_directory(self._h5_filename.parent)
        self._h5_file = h5py.File(self._h5_filename, "w")

        self._chemical_system = chemical_system
        self._last_configuration = None

        if selected_atoms is None:
            self._selected_atoms = list(self._chemical_system._atom_indices)
        else:
            self._selected_atoms = selected_atoms

        all_atoms = list(self._chemical_system.atom_list)
        for idx in self._selected_atoms:
            all_atoms[idx] = False

        self._dump_chemical_system()

        self._h5_file.create_group("/configuration")

        self._n_steps = n_steps

        self._n_atoms = self._chemical_system.total_number_of_atoms

        self._current_index = 0

        self._dtype = positions_dtype

        if self._n_atoms <= 1.5 * chunking_limit:
            self._chunk_tuple = (1, self._n_atoms, 3)
            self._padded_size = self._n_atoms
            self._chunking_limit = self._n_atoms
        else:
            self._chunk_tuple = (1, chunking_limit, 3)
            self._padded_size = (
                math.ceil(self._n_atoms / chunking_limit) * chunking_limit
            )
            self._chunking_limit = chunking_limit

        self._compression = compression

        if initial_charges is None:
            self._initial_charges = np.zeros(self._n_atoms)
        else:
            self._initial_charges = initial_charges

    def write_atom_properties(
        self, symbol: str, properties: Dict[str, Any], ptypes: Dict[str, str] = None
    ):
        if "atom_database" not in self._h5_file.keys():
            group = self._h5_file.create_group("/atom_database")
        else:
            group = self._h5_file["/atom_database"]
        string_dt = h5py.special_dtype(vlen=str)
        if "property_labels" not in group:
            label_dataset = group.create_dataset(
                "property_labels", data=200 * [""], dtype=string_dt
            )
        else:
            label_dataset = self._h5_file["/atom_database/property_labels"]
        if "property_types" not in group:
            type_dataset = group.create_dataset(
                "property_types", data=200 * [""], dtype=string_dt
            )
        else:
            type_dataset = self._h5_file["/atom_database/property_types"]
        next_index = 0
        for label in label_dataset[:]:
            if len(label) > 0:
                next_index += 1
            else:
                break
        properties["dummy"] = 0
        if symbol == "Du":
            properties["dummy"] = 1
        if "element" in properties.keys():
            if properties["element"] == "dummy":
                properties["dummy"] = 1
        new_labels = [str(x) for x in properties.keys()]
        if ptypes is None:
            ptypes = ATOMS_DATABASE._properties
        ptypes["dummy"] = "int"
        for label in new_labels:
            if label.encode("utf-8") not in label_dataset:
                label_dataset[next_index] = label
                type_dataset[next_index] = ptypes[label]
                next_index += 1
        mapping = {
            property_label.decode("utf-8"): index
            for index, property_label in enumerate(label_dataset[:])
        }
        atom_dataset = group.create_dataset(symbol, data=200 * [-1.0])
        for key, value in properties.items():
            try:
                float(value)
            except ValueError:
                continue
            except TypeError:
                continue
            else:
                atom_dataset[mapping[key]] = value
        try:
            colour = [int(x) for x in properties["color"].split(";")]
        except AttributeError:
            colour = [int(x) for x in properties["color"][0].split(";")]
        atom_dataset[mapping["color"]] = (
            0x10000 * colour[0] + 0x100 * colour[1] + colour[2]
        )

    def write_atom_database(
        self,
        symbols: List[str],
        database: "AtomsDatabase",
        optional_molecule_radii: Dict[str, float] = None,
    ):
        for atom_symbol in symbols:
            if database.has_atom(atom_symbol):
                property_dict = database.get_property_dict(atom_symbol)
            else:
                atom_dict = {}
                molecule_radius = 0.0
                for token in atom_symbol.split("_"):
                    symbol = ""
                    number = ""
                    noletters = True
                    for char in token:
                        if char.isnumeric():
                            if noletters:
                                symbol += char
                            else:
                                number += char
                        else:
                            symbol += char
                            noletters = False
                    atom_dict[symbol] = int(number)
                if optional_molecule_radii is not None:
                    molecule_radius = optional_molecule_radii.get(atom_symbol, 0.0)
                property_dict = create_average_atom(
                    atom_dict, database, radius_padding=molecule_radius
                )
            if hasattr(database, "_properties"):
                self.write_atom_properties(
                    atom_symbol, property_dict, database._properties
                )
            else:
                self.write_atom_properties(atom_symbol, property_dict)

    def write_standard_atom_database(self):
        symbols = list(np.unique(self._chemical_system.atom_list))
        database = ATOMS_DATABASE
        for atom_symbol in symbols:
            if database.has_atom(atom_symbol):
                property_dict = database.get_property_dict(atom_symbol)
            else:
                atom_dict = {}
                for token in atom_symbol.split("_"):
                    symbol = ""
                    number = ""
                    noletters = True
                    for char in token:
                        if char.isnumeric():
                            if noletters:
                                symbol += char
                            else:
                                number += char
                        else:
                            symbol += char
                            noletters = False
                    atom_dict[symbol] = int(number)
                property_dict = create_average_atom(atom_dict, database)
            self.write_atom_properties(atom_symbol, property_dict, database._properties)

    def _dump_chemical_system(self):
        """Dump the chemical system to the trajectory file."""

        self._chemical_system.serialize(self._h5_file)

    @property
    def chemical_system(self):
        return self._chemical_system

    def close(self):
        """Close the trajectory file"""
        self.validate_charges()

        n_atoms = self._chemical_system.total_number_of_atoms
        if self._last_configuration is not None:
            configuration_grp = self._h5_file["/configuration"]
            for k, v in self._last_configuration.variables.items():
                dset = configuration_grp.get(k, None)
                dset.resize((self._current_index, n_atoms, 3))
            try:
                unit_cell_dataset = self._h5_file["/unit_cell"]
            except KeyError:
                pass
            else:
                unit_cell_dataset.resize((self._current_index, 3, 3))
            time_dataset = self._h5_file["/time"]
            time_dataset.resize((self._current_index,))
        self._h5_file.close()

    def write_charges(self, charges: np.ndarray, index: int):
        """Writes atom charges into their dataset at the specified index.

        Parameters
        ----------
        charges : np.ndarray
            array of float values: atomic charges in proton charge units
        index : int
            number of the simulation frame
        """
        variable_charge_dset = self._h5_file.get("/configuration/charges", None)
        if variable_charge_dset is None:
            if self._compression in TrajectoryWriter.allowed_compression:
                variable_charge_dset = self._h5_file.create_dataset(
                    "/configuration/charges",
                    shape=(self._n_steps, self._padded_size),
                    chunks=(1, self._chunking_limit),
                    dtype=self._dtype,
                    compression=self._compression,
                )
            else:
                variable_charge_dset = self._h5_file.create_dataset(
                    "/configuration/charges",
                    shape=(self._n_steps, self._padded_size),
                    chunks=(1, self._chunking_limit),
                    dtype=self._dtype,
                )
        variable_charge_dset[index, : self._n_atoms] = charges

    def validate_charges(self):
        charge_is_constant = False
        variable_charge_dset = self._h5_file.get("/configuration/charges", None)
        if variable_charge_dset is None:
            charge_is_constant = True
            new_charge = self._initial_charges
        elif np.allclose(np.std(variable_charge_dset, axis=0), 0.0):
            charge_is_constant = True
            new_charge = np.mean(variable_charge_dset, axis=0)
        if charge_is_constant:
            constant_charge_dset = self._h5_file.create_dataset(
                "/charge",
                shape=(self._n_atoms,),
                dtype=self._dtype,
            )
            constant_charge_dset[:] = new_charge[: self._n_atoms]
            if variable_charge_dset is not None:
                del self._h5_file[variable_charge_dset.name]

    def dump_configuration(self, configuration, time, units=None):
        """Dump the chemical system configuration at a given time.

        :param time: the time
        :type time: float

        :param units: the units
        :type units: dict
        """

        if self._current_index >= self._n_steps:
            raise IndexError(
                f"The current index {self._current_index} is greater than the actual number of steps of the trajectory {self._n_steps}"
            )

        if configuration is None:
            return

        if units is None:
            units = {}

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
                        shape=(self._n_steps, self._padded_size, 3),
                        chunks=self._chunk_tuple,
                        dtype=self._dtype,
                        compression=self._compression,
                    )
                else:
                    dset = configuration_grp.create_dataset(
                        k,
                        shape=(self._n_steps, self._padded_size, 3),
                        chunks=self._chunk_tuple,
                        dtype=self._dtype,
                    )
                dset.attrs["units"] = units.get(k, "")
            dset[self._current_index, : self._n_atoms] = data

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
                "time", shape=(self._n_steps,), chunks=(1,), dtype=np.float64
            )
            time_dset.attrs["units"] = units.get("time", "")
        time_dset[self._current_index] = time

        self._current_index += 1
        self._last_configuration = configuration


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
        chemical_entity: List[int],
        reference,
        first=0,
        last=None,
        step=1,
    ):
        """Constructor.

        :param trajectory: the input trajectory
        :type trajectory: MDANSE.Trajectory.Trajectory
        :param chemical_entity: the chemical enitty for which the Rigig-Body trajectory should be computed
        :type chemical_entity: MDANSE.Chemistry.ChemicalSystem.ChemicalEntity
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

        masses = [ATOMS_DATABASE.get_atom_property(at, "atomic_weight") for at in atoms]

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
            r_ref[i] = reference["coordinates"][i, :] - ref_com

        unit_cells, inverse_unit_cells = self._trajectory.get_unit_cells()
        if unit_cells is not None:
            unit_cells = unit_cells[first:last:step, :, :]
            inverse_unit_cells = inverse_unit_cells[first:last:step, :, :]

        for i, at in enumerate(atoms):
            r = self._trajectory.read_atomic_trajectory(i, first, last, step, True)
            r = r - rcms

            r = r[:, np.newaxis, :]
            # Fold coordinates doesn't exist?
            # r = fold_coordinates.fold_coordinates(
            #     r, unit_cells, inverse_unit_cells, True
            # )
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

    # nFrames = len(range(first, last, step))

    # serie = np.zeros((nFrames, 3), dtype=dtype)

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

    # from MDANSE.Chemistry.ChemicalSystem import Atom
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
    from MDANSE.Chemistry.ChemicalEntity import Atom
    from MDANSE.MolecularDynamics.Configuration import RealConfiguration

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
