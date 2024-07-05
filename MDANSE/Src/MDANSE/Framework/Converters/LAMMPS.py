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
import logging
import collections
import numpy as np

import h5py

from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Graph import Graph
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    PeriodicRealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.Framework.AtomMapping import get_element_from_mapping


LOG = logging.getLogger("MDANSE")


class LAMMPSTrajectoryFileError(Error):
    pass


class LAMMPSReader:

    def __init__(self, *args, **kwargs):
        self._units = kwargs.get("lammps_units", "real")
        self._timestep = kwargs.get("timestep", 1.0)
        self._fold = kwargs.get("fold_coordinates", False)
        self.set_units(self._units)
        self._file = None

    def close(self):
        try:
            self._file.close()
        except:
            LOG.error(f"Could not close file: {self._file}")

    def set_output(self, output_trajectory):
        self._trajectory = output_trajectory

    def set_units(self, lammps_units):
        self._energy_unit = ""
        self._time_unit = ""
        self._length_unit = ""
        self._velocity_unit = ""
        self._mass_unit = ""
        if lammps_units == "real":
            self._energy_unit = "kcal_per_mole"
            self._time_unit = "fs"
            self._length_unit = "ang"
            self._velocity_unit = "ang/fs"
            self._mass_unit = "uma"
        elif lammps_units == "metal":
            self._energy_unit = "eV"
            self._time_unit = "ps"
            self._length_unit = "ang"
            self._velocity_unit = "ang/ps"
            self._mass_unit = "uma"
        elif lammps_units == "si":
            self._energy_unit = "J"
            self._time_unit = "s"
            self._length_unit = "m"
            self._velocity_unit = "m/s"
            self._mass_unit = "kg"
        elif lammps_units == "cgs":
            self._energy_unit = "erg"  # this will fail
            self._time_unit = "s"
            self._length_unit = "cm"
            self._velocity_unit = "cm/s"
            self._mass_unit = "g"
        elif lammps_units == "electron":
            self._energy_unit = "Ha"
            self._time_unit = "fs"
            self._length_unit = "Bohr"
            self._velocity_unit = "ang/fs"
            self._mass_unit = "uma"
        elif lammps_units == "micro":
            self._energy_unit = "pg*m/s"
            self._time_unit = "us"
            self._length_unit = "um"
            self._velocity_unit = "m/s"
            self._mass_unit = "pg"
        elif lammps_units == "nano":
            self._energy_unit = "ag*m/s"
            self._time_unit = "ns"
            self._length_unit = "nm"
            self._velocity_unit = "m/s"
            self._mass_unit = "ag"


class LAMMPScustom(LAMMPSReader):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_time_steps(self, filename: str) -> int:
        number_of_steps = 0
        self.open_file(filename)
        if number_of_steps == 0:
            for line in self._file:
                if line.startswith("ITEM: TIMESTEP"):
                    number_of_steps += 1
        self.close()
        return number_of_steps

    def open_file(self, filename: str):
        self._file = open(filename, "r")
        self._start = 0

    def parse_first_step(self, aliases, config):

        self._itemsPosition = collections.OrderedDict()

        comp = -1

        while True:
            line = self._file.readline()
            comp += 1

            if not line:
                break

            if line.startswith("ITEM: TIMESTEP"):
                self._itemsPosition["TIMESTEP"] = [comp + 1, comp + 2]
                continue

            elif line.startswith("ITEM: BOX BOUNDS"):
                self._itemsPosition["BOX BOUNDS"] = [comp + 1, comp + 4]
                continue

            elif line.startswith("ITEM: ATOMS"):
                keywords = line.split()[2:]

                self._id = keywords.index("id")
                self._type = keywords.index("type")

                # Field name is <x,y,z> or cd ..<x,y,z>u if real coordinates and <x,y,z>s if fractional ones
                self._fractionalCoordinates = False
                try:
                    self._x = keywords.index("x")
                    self._y = keywords.index("y")
                    self._z = keywords.index("z")
                except ValueError:
                    try:
                        self._x = keywords.index("xu")
                        self._y = keywords.index("yu")
                        self._z = keywords.index("zu")
                    except ValueError:
                        try:
                            self._x = keywords.index("xs")
                            self._y = keywords.index("ys")
                            self._z = keywords.index("zs")
                            self._fractionalCoordinates = True
                        except ValueError:
                            raise LAMMPSTrajectoryFileError(
                                "No coordinates could be found in the trajectory"
                            )

                self._rankToName = {}

                g = Graph()
                self._itemsPosition["ATOMS"] = [comp + 1, comp + self._nAtoms + 1]
                for i in range(self._nAtoms):
                    temp = self._file.readline().split()
                    idx = int(temp[self._id]) - 1
                    ty = int(temp[self._type]) - 1
                    label = str(config["elements"][ty][0])
                    mass = str(config["elements"][ty][1])
                    name = "{:s}_{:d}".format(str(config["elements"][ty][0]), idx)
                    self._rankToName[int(temp[0]) - 1] = name
                    g.add_node(idx, label=label, mass=mass, atomName=name)

                if config["n_bonds"] is not None:
                    for idx1, idx2 in config["bonds"]:
                        g.add_link(idx1, idx2)

                chemicalSystem = ChemicalSystem()

                for cluster in g.build_connected_components():
                    if len(cluster) == 1:
                        node = cluster.pop()
                        try:
                            element = get_element_from_mapping(
                                aliases, node.label, mass=node.mass
                            )
                            obj = Atom(symbol=element, name=node.atomName)
                        except TypeError:
                            LOG.error("EXCEPTION in LAMMPS loader")
                            LOG.error(f"node.element = {node.element}")
                            LOG.error(f"node.atomName = {node.atomName}")
                            LOG.error(f"rankToName = {self._rankToName}")
                        obj.index = node.name
                    else:
                        atList = []
                        for atom in cluster:
                            element = get_element_from_mapping(
                                aliases, atom.label, mass=atom.mass
                            )
                            at = Atom(symbol=element, name=atom.atomName)
                            atList.append(at)
                        c = collections.Counter([at.label for at in cluster])
                        name = "".join(
                            ["{:s}{:d}".format(k, v) for k, v in sorted(c.items())]
                        )
                        obj = AtomCluster(name, atList)

                    chemicalSystem.add_chemical_entity(obj)
                self._last = comp + self._nAtoms + 1

                break

            elif line.startswith("ITEM: NUMBER OF ATOMS"):
                self._nAtoms = int(self._file.readline())
                comp += 1
                continue
        return chemicalSystem

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        for _ in range(self._itemsPosition["TIMESTEP"][0]):
            line = self._file.readline()
            if not line:
                return index, None

        time = (
            float(self._file.readline())
            * self._timestep
            * measure(1.0, self._time_unit).toval("ps")
        )

        for _ in range(
            self._itemsPosition["TIMESTEP"][1], self._itemsPosition["BOX BOUNDS"][0]
        ):
            self._file.readline()

        unitCell = np.zeros((9), dtype=np.float64)
        temp = [float(v) for v in self._file.readline().split()]
        if len(temp) == 2:
            xlo, xhi = temp
            xy = 0.0
        elif len(temp) == 3:
            xlo, xhi, xy = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for A vector components")

        temp = [float(v) for v in self._file.readline().split()]
        if len(temp) == 2:
            ylo, yhi = temp
            xz = 0.0
        elif len(temp) == 3:
            ylo, yhi, xz = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for B vector components")

        temp = [float(v) for v in self._file.readline().split()]
        if len(temp) == 2:
            zlo, zhi = temp
            yz = 0.0
        elif len(temp) == 3:
            zlo, zhi, yz = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for C vector components")

        # The ax component.
        unitCell[0] = xhi - xlo

        # The bx and by components.
        unitCell[3] = xy
        unitCell[4] = yhi - ylo

        # The cx, cy and cz components.
        unitCell[6] = xz
        unitCell[7] = yz
        unitCell[8] = zhi - zlo

        unitCell = np.reshape(unitCell, (3, 3))

        unitCell *= measure(1.0, self._length_unit).toval("nm")
        unitCell = UnitCell(unitCell)

        for _ in range(
            self._itemsPosition["BOX BOUNDS"][1], self._itemsPosition["ATOMS"][0]
        ):
            self._file.readline()

        coords = np.empty(
            (self._trajectory.chemical_system.number_of_atoms, 3), dtype=np.float64
        )

        for i, _ in enumerate(
            range(self._itemsPosition["ATOMS"][0], self._itemsPosition["ATOMS"][1])
        ):
            temp = self._file.readline().split()
            idx = self._nameToIndex[self._rankToName[int(temp[0]) - 1]]
            coords[idx, :] = np.array(
                [temp[self._x], temp[self._y], temp[self._z]], dtype=np.float64
            )

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system, coords, unitCell
            )
            realConf = conf.to_real_configuration()
        else:
            coords *= measure(1.0, self._length_unit).toval("nm")
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, coords, unitCell
            )

        if self._fold:
            # The whole configuration is folded in to the simulation box.
            realConf.fold_coordinates()

        self._trajectory.chemical_system.configuration = realConf

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
        )

        self._start += self._last

        return index, self._start


class LAMMPSxyz(LAMMPSReader):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._full_cell = None

    def get_time_steps(self, filename: str) -> int:
        number_of_steps = 0
        self.open_file(filename)
        if number_of_steps == 0:
            for line in self._file:
                if len(line.split()) == 1:
                    number_of_steps += 1
        self.close()
        return number_of_steps

    def open_file(self, filename: str):
        self._file = open(filename, "r")

    def read_any_step(self):

        line = self._file.readline()
        number_of_atoms = int(line)
        line = self._file.readline()
        timestep = int(line.split()[-1])

        positions = np.empty((number_of_atoms, 3))
        atom_types = np.empty(number_of_atoms, dtype=int)

        for at_num in range(number_of_atoms):

            line = self._file.readline()

            if not line:
                break

            toks = line.split()

            if len(toks) == 4:
                atom_id = int(toks[0])
                atom_pos = [float(x) for x in toks[1:]]
                positions[at_num] = atom_pos
                atom_types[at_num] = atom_id

        return timestep, atom_types, positions

    def parse_first_step(self, aliases, config):

        _, atom_types, positions = self.read_any_step()

        self._nAtoms = len(atom_types)

        self._fractionalCoordinates = False
        unit_cell = config["unit_cell"]
        span = np.max(positions, axis=0) - np.min(positions, axis=0)
        cellspan = np.linalg.norm(unit_cell, axis=1)
        if np.allclose(cellspan, [0, 0, 0]):
            self._fractionalCoordinates = False
            full_cell = None
        elif np.allclose(span, [1.0, 1.0, 1.0], rtol=0.1, atol=0.1):
            if np.allclose(cellspan, [1.0, 1.0, 1.0], rtol=0.1, atol=0.1):
                self._fractionalCoordinates = False
            else:
                self._fractionalCoordinates = True
            full_cell = unit_cell
        else:
            self._fractionalCoordinates = False
            multiplicity = np.round(np.abs(span / cellspan)).astype(int)
            full_cell = unit_cell * multiplicity.reshape((3, 1))

        full_cell *= measure(1.0, self._length_unit).toval("nm")

        self._full_cell = full_cell

        self._rankToName = {}

        g = Graph()
        for i in range(self._nAtoms):
            idx = i
            ty = atom_types[i] - 1
            label = str(config["elements"][ty][0])
            mass = str(config["elements"][ty][1])
            name = "{:s}_{:d}".format(str(config["elements"][ty][0]), idx)
            self._rankToName[idx] = name
            g.add_node(idx, label=label, mass=mass, atomName=name)

        if config["n_bonds"] is not None:
            for idx1, idx2 in config["bonds"]:
                g.add_link(idx1, idx2)

        chemicalSystem = ChemicalSystem()

        for cluster in g.build_connected_components():
            if len(cluster) == 1:
                node = cluster.pop()
                try:
                    element = get_element_from_mapping(
                        aliases, node.label, mass=node.mass
                    )
                    obj = Atom(symbol=element, name=node.atomName)
                except TypeError:
                    LOG.error("EXCEPTION in LAMMPS loader")
                    LOG.error(f"node.element = {node.element}")
                    LOG.error(f"node.atomName = {node.atomName}")
                    LOG.error(f"rankToName = {self._rankToName}")
                obj.index = node.name
            else:
                atList = []
                for atom in cluster:
                    element = get_element_from_mapping(
                        aliases, atom.label, mass=atom.mass
                    )
                    at = Atom(symbol=element, name=atom.atomName)
                    atList.append(at)
                c = collections.Counter([at.label for at in cluster])
                name = "".join(["{:s}{:d}".format(k, v) for k, v in sorted(c.items())])
                obj = AtomCluster(name, atList)

            chemicalSystem.add_chemical_entity(obj)

        return chemicalSystem

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        try:
            timestep, _, positions = self.read_any_step()
        except ValueError:
            return

        unitCell = UnitCell(self._full_cell)
        time = timestep * self._timestep * measure(1.0, self._time_unit).toval("ps")

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system, positions, unitCell
            )
            realConf = conf.to_real_configuration()
        else:
            positions *= measure(1.0, self._length_unit).toval("nm")
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, positions, unitCell
            )

        if self._fold:
            # The whole configuration is folded in to the simulation box.
            realConf.fold_coordinates()

        self._trajectory.chemical_system.configuration = realConf

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
        )

        return index, 0


class LAMMPSh5md(LAMMPSReader):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_time_steps(self, filename: str) -> int:
        number_of_steps = 0
        self.open_file(filename)
        number_of_steps = len(self._file["/particles/all/position/time"][:])
        self.close()
        return number_of_steps

    def open_file(self, filename: str):
        self._file = h5py.File(filename, "r")

    def parse_first_step(self, aliases, config):

        try:
            atom_types = self._file["/particles/all/species/value"][0]
        except KeyError:
            atom_types = config["atom_types"]

        self._nAtoms = len(self._file["/particles/all/position/value"][0])

        if len(atom_types) < self._nAtoms:
            atom_types = int(round(self._nAtoms / len(atom_types))) * list(atom_types)

        self._fractionalCoordinates = False
        cell_edges = self._file["/particles/all/box/edges/value"][0]
        full_cell = np.array(
            [[cell_edges[0], 0, 0], [0, cell_edges[1], 0], [0, 0, cell_edges[2]]]
        )

        full_cell *= measure(1.0, self._length_unit).toval("nm")

        self._full_cell = full_cell

        self._rankToName = {}

        g = Graph()
        for i in range(self._nAtoms):
            idx = i
            ty = atom_types[i] - 1
            label = str(config["elements"][ty][0])
            mass = str(config["elements"][ty][1])
            name = "{:s}_{:d}".format(str(config["elements"][ty][0]), idx)
            self._rankToName[idx] = name
            g.add_node(idx, label=label, mass=mass, atomName=name)

        if config["n_bonds"] is not None:
            for idx1, idx2 in config["bonds"]:
                g.add_link(idx1, idx2)

        chemicalSystem = ChemicalSystem()

        for cluster in g.build_connected_components():
            if len(cluster) == 1:
                node = cluster.pop()
                try:
                    element = get_element_from_mapping(
                        aliases, node.label, mass=node.mass
                    )
                    obj = Atom(symbol=element, name=node.atomName)
                except TypeError:
                    LOG.error("EXCEPTION in LAMMPS loader")
                    LOG.error(f"node.element = {node.element}")
                    LOG.error(f"node.atomName = {node.atomName}")
                    LOG.error(f"rankToName = {self._rankToName}")
                obj.index = node.name
            else:
                atList = []
                for atom in cluster:
                    element = get_element_from_mapping(
                        aliases, atom.label, mass=atom.mass
                    )
                    at = Atom(symbol=element, name=atom.atomName)
                    atList.append(at)
                c = collections.Counter([at.label for at in cluster])
                name = "".join(["{:s}{:d}".format(k, v) for k, v in sorted(c.items())])
                obj = AtomCluster(name, atList)

            chemicalSystem.add_chemical_entity(obj)

        return chemicalSystem

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        positions = self._file["/particles/all/position/value"][index]
        timestep = self._file["/particles/all/position/step"][index]

        unitCell = UnitCell(self._full_cell)
        time = timestep * self._timestep * measure(1.0, self._time_unit).toval("ps")

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system, positions, unitCell
            )
            realConf = conf.to_real_configuration()
        else:
            positions *= measure(1.0, self._length_unit).toval("nm")
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, positions, unitCell
            )

        if self._fold:
            # The whole configuration is folded in to the simulation box.
            realConf.fold_coordinates()

        self._trajectory.chemical_system.configuration = realConf

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
        )

        return index, 0


class LAMMPS(Converter):
    """
    Converts a LAMMPS trajectory to a HDF trajectory.
    """

    label = "LAMMPS"

    settings = collections.OrderedDict()
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
            "choices": ["real", "metal", "si", "cgs", "electron", "micro", "nano"],
            "default": "real",
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
    settings["output_file"] = (
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
        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self._lammpsConfig = self.configuration["config_file"]

        self._lammps_units = self.configuration["lammps_units"]["value"]
        self._lammps_format = self.configuration["trajectory_format"]["value"]

        self._reader = self.create_reader(self._lammps_format)

        self._reader.set_units(self._lammps_units)
        self._chemicalSystem = self.parse_first_step(self._atomicAliases)

        if self.numberOfSteps == 0:
            self.numberOfSteps = self._reader.get_time_steps(
                self.configuration["trajectory_file"]["value"]
            )

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemicalSystem,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_file"]["dtype"],
            compression=self.configuration["output_file"]["compression"],
        )

        self._reader._nameToIndex = dict(
            [(at.name, at.index) for at in self._trajectory.chemical_system.atom_list]
        )

        self._start = 0
        self._reader.open_file(self.configuration["trajectory_file"]["value"])
        self._reader.set_output(self._trajectory)

    def create_reader(self, trajectory_type: str) -> "LAMMPSReader":
        reader = None
        if trajectory_type == "custom":
            reader = LAMMPScustom(
                lammps_units=self._lammps_units,
                timestep=self.configuration["time_step"]["value"],
                fold_coordinates=self.configuration["fold"]["value"],
            )
        if trajectory_type == "xyz":
            reader = LAMMPSxyz(
                lammps_units=self._lammps_units,
                timestep=self.configuration["time_step"]["value"],
                fold_coordinates=self.configuration["fold"]["value"],
            )
        if trajectory_type == "h5md":
            reader = LAMMPSh5md(
                lammps_units=self._lammps_units,
                timestep=self.configuration["time_step"]["value"],
                fold_coordinates=self.configuration["fold"]["value"],
            )
        return reader

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        val1, val2 = self._reader.run_step(index)

        self._start = val2

        return val1, None

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x:
        @type x: any.
        """

        pass

    def finalize(self):
        """
        Finalize the job.
        """

        self._reader.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(LAMMPS, self).finalize()

    def parse_first_step(self, aliases):
        self._reader.open_file(self.configuration["trajectory_file"]["value"])
        chemicalSystem = self._reader.parse_first_step(aliases, self._lammpsConfig)
        self._reader.close()
        return chemicalSystem
