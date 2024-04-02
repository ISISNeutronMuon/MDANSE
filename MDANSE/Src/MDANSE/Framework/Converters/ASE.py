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
import collections
import os

from ase.io import iread, read
from ase.atoms import Atoms as ASEAtoms
from ase.io.trajectory import Trajectory as ASETrajectory
import numpy as np
import h5py

from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter, InteractiveConverter
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Graph import Graph
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class ASETrajectoryFileError(Error):
    pass


class ASE(Converter):
    """
    Converts any trajectory to a HDF trajectory using the ASE io module.
    """

    label = "ASE"

    settings = collections.OrderedDict()
    settings["trajectory_file"] = (
        "ASEFileConfigurator",
        {
            "label": "Any MD trajectory file",
            "default": "INPUT_FILENAME.traj",
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "trajectory_file"},
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {"label": "Time step", "default": 1.0, "mini": 1.0e-9},
    )
    settings["time_unit"] = (
        "SingleChoiceConfigurator",
        {"label": "Time step unit", "choices": ["fs", "ps", "ns"], "default": "fs"},
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
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_file"] = (
        "OutputTrajectoryConfigurator",
        {
            "label": "MDANSE trajectory (filename, format)",
            "formats": ["MDTFormat"],
            "root": "config_file",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """
        self._isPeriodic = None
        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self._timestep = float(self.configuration["time_step"]["value"]) * measure(
            1.0, self.configuration["time_unit"]["value"]
        ).toval("ps")

        self.parse_first_step(self._atomicAliases)
        print(f"isPeriodic after parse_first_step: {self._isPeriodic}")
        self._start = 0

        if self.numberOfSteps < 1:
            self.numberOfSteps = self._total_number_of_steps

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemicalSystem,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_file"]["dtype"],
            compression=self.configuration["output_file"]["compression"],
        )

        self._nameToIndex = dict(
            [(at.name, at.index) for at in self._trajectory.chemical_system.atom_list]
        )

        print(f"total steps: {self.numberOfSteps}")

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        try:
            frame = self._input[index]
        except TypeError:
            frame = next(self._input)
        else:
            print("ASE using the slower way")
            frame = read(self.configuration["trajectory_file"]["value"], index=index)
        time = self._timeaxis[index]

        if self._isPeriodic:
            unitCell = frame.cell.array
            print(f"Unit cell from frame: {unitCell}")

            unitCell *= measure(1.0, "ang").toval("nm")
            unitCell = UnitCell(unitCell)

        coords = frame.get_positions()
        coords *= measure(1.0, "ang").toval("nm")

        if self._isPeriodic:
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, coords, unitCell
            )
            if self._configuration["fold"]["value"]:
                realConf.fold_coordinates()
        else:
            realConf = RealConfiguration(
                self._trajectory.chemical_system,
                coords,
            )

        self._trajectory.chemical_system.configuration = realConf

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
        )

        return index, None

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

        self._input.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(ASE, self).finalize()

    def parse_first_step(self, mapping):
        try:
            self._input = ASETrajectory(self.configuration["trajectory_file"]["value"])
        except:
            first_frame = read(self.configuration["trajectory_file"]["value"], index=0)
            last_iterator = 0
            generator = iread(self.configuration["trajectory_file"]["value"])
            for _ in generator:
                last_iterator += 1
            generator.close()
            self._input = iread(
                self.configuration["trajectory_file"]["value"]  # , index="[:]"
            )
            self._total_number_of_steps = last_iterator
        else:
            first_frame = self._input[0]
            self._total_number_of_steps = len(self._input)

        self._timeaxis = self._timestep * np.arange(self._total_number_of_steps)

        if self._isPeriodic is None:
            self._isPeriodic = np.all(first_frame.get_pbc())
        print(f"PBC in first frame = {first_frame.get_pbc()}")

        g = Graph()

        element_count = {}
        element_list = first_frame.get_chemical_symbols()

        self._nAtoms = len(element_list)

        self._chemicalSystem = ChemicalSystem()

        for atnum, element in enumerate(element_list):
            if element in element_count.keys():
                element_count[element] += 1
            else:
                element_count[element] = 1
            g.add_node(atnum, element=element, atomName=f"{element}_{atnum+1}")

        for cluster in g.build_connected_components():
            if len(cluster) == 1:
                node = cluster.pop()
                try:
                    element = get_element_from_mapping(mapping, node.element)
                    obj = Atom(element, name=node.atomName)
                except TypeError:
                    print("EXCEPTION in ASE loader")
                    print(f"node.element = {node.element}")
                    print(f"node.atomName = {node.atomName}")
                    print(f"rankToName = {self._rankToName}")
                obj.index = node.name
            else:
                atList = []
                for atom in cluster:
                    element = get_element_from_mapping(mapping, atom.element)
                    at = Atom(symbol=element, name=atom.atomName)
                    atList.append(at)
                c = collections.Counter([at.element for at in cluster])
                name = "".join(["{:s}{:d}".format(k, v) for k, v in sorted(c.items())])
                obj = AtomCluster(name, atList)

            self._chemicalSystem.add_chemical_entity(obj)


class ASEInteractiveConverter(InteractiveConverter):
    """
    Converts any trajectory to a HDF trajectory using the ASE io module.
    """

    category = ("InteractiveConverter",)

    label = "ASE"

    input_files = collections.OrderedDict()
    settings = collections.OrderedDict()
    output_files = collections.OrderedDict()

    input_files["trajectory_file"] = (
        "InputFileConfigurator",
        {
            "label": "Any MD trajectory file",
            "default": os.path.join(
                "..",
                "..",
                "..",
                "Data",
                "Trajectories",
                "LAMMPS",
                "glycyl_L_alanine_charmm.lammps",
            ),
        },
    )
    input_files["configuration_file"] = (
        "InputFileConfigurator",
        {
            "label": "An optional structure/configuration file",
            "default": os.path.join(
                "..",
                "..",
                "..",
                "Data",
                "Trajectories",
                "LAMMPS",
                "glycyl_L_alanine_charmm.lammps",
            ),
        },
    )

    settings["time_step"] = (
        "FloatConfigurator",
        {"label": "time step (fs)", "default": 1.0, "mini": 1.0e-9},
    )
    settings["time_unit"] = (
        "SingleChoiceConfigurator",
        {"label": "time step unit", "choices": ["fs", "ps", "ns"], "default": "fs"},
    )
    settings["n_steps"] = (
        "IntegerConfigurator",
        {
            "label": "number of time steps (0 for automatic detection)",
            "default": 0,
            "mini": 0,
        },
    )

    output_files["output_file"] = (
        "OutputTrajectoryConfigurator",
        {"format": "MDTFormat", "root": "config_file"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)

        self.pages.append(self.input_files)
        self.pages.append(self.settings)
        self.pages.append(self.output_files)

    def initialize(self):
        """
        Initialize the job.
        """

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self.parse_first_step()

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemicalSystem,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_file"]["dtype"],
            compression=self.configuration["output_file"]["compression"],
        )

        self._nameToIndex = dict(
            [(at.name, at.index) for at in self._trajectory.chemical_system.atom_list]
        )

        self._start = 0

        float(self.configuration["time_step"]["value"]) * measure(
            1.0, self.configuration["time_unit"]["value"]
        )

    def getFieldValues(self, page_number: int = 0, values: dict = None) -> dict:
        """Returns the values of the GUI fields
        on the Nth page of the wizard interface.
        It is intended to be used for updating
        the values shown by the GUI, since the GUI
        will be initialised using default values.
        The page numbering starts from 0.
        """
        raise NotImplementedError

    def setFieldValues(self, page_number: int = 0, values: dict = None) -> None:
        """Accepts the values of the input fields from the
        Nth page of the wizard. It uses the same key values
        as those returned by the getFields method.
        """
        raise NotImplementedError

    def primaryInputs(self) -> dict:
        """Returns the list of inputs needed for the first page
        of the wizard. These should typically be the names of
        the input files passed to the converter.
        """
        return self.input_files

    def secondaryInputs(self) -> dict:
        """Returns the list of inputs needed for the second page
        of the wizard. These should typically be the parameters
        specifying how to read the trajectory: time step, number
        of frames, frame step, etc.
        """
        return self.settings

    def finalInputs(self) -> dict:
        """Normally this should just give the user a chance
        to input the name of the (converted) output trajectory.
        It is done at the last step, since the user may want
        to base the name on the decisions they made for the
        input parameters.
        """
        return self.output_files

    def systemSummary(self) -> dict:
        """Returns all the information about the simulation
        that is currently stored by the converter. This will
        allow the users to verify if all the information was
        read correctly (or at all). This function must also
        place default values in the fields related to the
        parameters that could not be read.
        """
        return {"Mock Numbers": [1, 2, 3]}

    def guessFromConfig(self, fname: str):
        """Tries to retrieve as much information as possible
        about the simulation to be converted from a config file.

        Arguments
        ---------

        fname (str) - name of the config file to be opened.
        """
        temp = read(fname)
        self.parseASE(temp)

    def guessFromTrajectory(self, fname: str):
        """Tries to retrieve as much information as possible
        about the simulation to be converted from a trajectory file.
        This will typically mean that the first frame of the trajectory
        will be read and parsed, while the rest of it will be ignored for now.

        Arguments
        ---------

        fname (str) - name of the trajectory file to be opened.
        """
        gen = iread(fname, 0)  # gen is a generator which can yield Atoms objects

        for i in gen[:1]:
            temp = i  # now temp is the Atoms object from the first frame

        self.parseASE(temp)

    def parseASE(self, input: ASEAtoms):
        g = Graph()

        element_count = {}
        element_list = input.get_chemical_symbols()
        id_list = np.arange(len(element_list)) + 1

        self._nAtoms = len(element_list)

        self._chemicalSystem = ChemicalSystem()

        for atnum, element in enumerate(element_list):
            if element in element_count.keys():
                element_count[element] += 1
            else:
                element_count[element] = 1
            g.add_node(atnum, element=element, atomName=f"{element}_{atnum+1}")

        for cluster in g.build_connected_components():
            if len(cluster) == 1:
                node = cluster.pop()
                try:
                    obj = Atom(node.element, name=node.atomName)
                except TypeError:
                    print("EXCEPTION in LAMMPS loader")
                    print(f"node.element = {node.element}")
                    print(f"node.atomName = {node.atomName}")
                    print(f"rankToName = {self._rankToName}")
                obj.index = node.name
            else:
                atList = []
                for atom in cluster:
                    at = Atom(symbol=atom.element, name=atom.atomName)
                    atList.append(at)
                c = collections.Counter([at.element for at in cluster])
                name = "".join(["{:s}{:d}".format(k, v) for k, v in sorted(c.items())])
                obj = AtomCluster(name, atList)

            self._chemicalSystem.add_chemical_entity(obj)

    def finalize(self):
        """I am not sure if this function is necessary. The specific converters
        seem to override it with their own version.
        """

        if not hasattr(self, "_trajectory"):
            return

        try:
            output_file = h5py.File(self._trajectory.filename, "a")
            # f = netCDF4.Dataset(self._trajectory.filename,'a')
        except:
            return

        try:
            if "time" in output_file.variables:
                output_file.variables["time"].units = "ps"
                output_file.variables["time"].axis = "time"
                output_file.variables["time"].name = "time"

            if "box_size" in output_file.variables:
                output_file.variables["box_size"].units = "ps"
                output_file.variables["box_size"].axis = "time"
                output_file.variables["box_size"].name = "box_size"

            if "configuration" in output_file.variables:
                output_file.variables["configuration"].units = "nm"
                output_file.variables["configuration"].axis = "time"
                output_file.variables["configuration"].name = "configuration"

            if "velocities" in output_file.variables:
                output_file.variables["velocities"].units = "nm/ps"
                output_file.variables["velocities"].axis = "time"
                output_file.variables["velocities"].name = "velocities"

            if "gradients" in output_file.variables:
                output_file.variables["gradients"].units = "amu*nm/ps"
                output_file.variables["gradients"].axis = "time"
                output_file.variables["gradients"].name = "gradients"
        finally:
            output_file.close()

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        self._input = iread(self.configuration["trajectory_file"]["value"])

        for stepnum, frame in enumerate(self._input):
            time = stepnum * self._timestep

        for _ in range(self._itemsPosition["TIMESTEP"][0]):
            line = self._lammps.readline()
            if not line:
                return index, None

        time = (
            float(self._lammps.readline())
            * self.configuration["time_step"]["value"]
            * measure(1.0, "fs").toval("ps")
        )

        for _ in range(
            self._itemsPosition["TIMESTEP"][1], self._itemsPosition["BOX BOUNDS"][0]
        ):
            self._lammps.readline()

        unitCell = np.zeros((9), dtype=np.float64)
        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            xlo, xhi = temp
            xy = 0.0
        elif len(temp) == 3:
            xlo, xhi, xy = temp
        else:
            raise ASETrajectoryFileError("Bad format for A vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            ylo, yhi = temp
            xz = 0.0
        elif len(temp) == 3:
            ylo, yhi, xz = temp
        else:
            raise ASETrajectoryFileError("Bad format for B vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            zlo, zhi = temp
            yz = 0.0
        elif len(temp) == 3:
            zlo, zhi, yz = temp
        else:
            raise ASETrajectoryFileError("Bad format for C vector components")

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

        unitCell *= measure(1.0, "ang").toval("nm")
        unitCell = UnitCell(unitCell)

        for _ in range(
            self._itemsPosition["BOX BOUNDS"][1], self._itemsPosition["ATOMS"][0]
        ):
            self._lammps.readline()

        coords = np.empty(
            (self._trajectory.chemical_system.number_of_atoms, 3), dtype=np.float64
        )

        for i, _ in enumerate(
            range(self._itemsPosition["ATOMS"][0], self._itemsPosition["ATOMS"][1])
        ):
            temp = self._lammps.readline().split()
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
            coords *= measure(1.0, "ang").toval("nm")
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, coords, unitCell
            )

        if self.configuration["fold"]["value"]:
            # The whole configuration is folded in to the simulation box.
            realConf.fold_coordinates()

        self._trajectory.chemical_system.configuration = realConf

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
        )

        self._start += self._last

        return index, None

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

        self._lammps.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(ASE, self).finalize()

    def parse_first_step(self):
        self._input = iread(self.configuration["trajectory_file"]["value"], index=0)

        for i in self._input[:1]:
            frame = i

        g = Graph()

        element_count = {}
        element_list = frame.get_chemical_symbols()
        id_list = np.arange(len(element_list)) + 1

        self._nAtoms = len(element_list)

        self._chemicalSystem = ChemicalSystem()

        for atnum, element in enumerate(element_list):
            if element in element_count.keys():
                element_count[element] += 1
            else:
                element_count[element] = 1
            g.add_node(atnum, element=element, atomName=f"{element}_{atnum+1}")

        for cluster in g.build_connected_components():
            if len(cluster) == 1:
                node = cluster.pop()
                try:
                    obj = Atom(node.element, name=node.atomName)
                except TypeError:
                    print("EXCEPTION in LAMMPS loader")
                    print(f"node.element = {node.element}")
                    print(f"node.atomName = {node.atomName}")
                    print(f"rankToName = {self._rankToName}")
                obj.index = node.name
            else:
                atList = []
                for atom in cluster:
                    at = Atom(symbol=atom.element, name=atom.atomName)
                    atList.append(at)
                c = collections.Counter([at.element for at in cluster])
                name = "".join(["{:s}{:d}".format(k, v) for k, v in sorted(c.items())])
                obj = AtomCluster(name, atList)

            self._chemicalSystem.add_chemical_entity(obj)
