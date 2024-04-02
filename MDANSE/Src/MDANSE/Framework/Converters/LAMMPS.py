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
import numpy as np

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


class LAMMPSTrajectoryFileError(Error):
    pass


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
            "wildcard": "Config files (*.config)|*.config|All files|*",
            "default": "INPUT_FILENAME.config",
        },
    )
    settings["trajectory_file"] = (
        "InputFileConfigurator",
        {
            "label": "LAMMPS trajectory file",
            "wildcard": "lammps files (*.lammps)|*.lammps|All files|*",
            "default": "INPUT_FILENAME.lammps",
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
        {"label": "Time step (fs)", "default": 1.0, "mini": 1.0e-9},
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

        self.parse_first_step(self._atomicAliases)

        # Estimate number of steps if needed
        if self.numberOfSteps == 0:
            self.numberOfSteps = 1
            for line in self._lammps:
                if line.startswith("ITEM: TIMESTEP"):
                    self.numberOfSteps += 1

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

        self._lammps.seek(0, 0)

        self._start = 0

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

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
            raise LAMMPSTrajectoryFileError("Bad format for A vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
        if len(temp) == 2:
            ylo, yhi = temp
            xz = 0.0
        elif len(temp) == 3:
            ylo, yhi, xz = temp
        else:
            raise LAMMPSTrajectoryFileError("Bad format for B vector components")

        temp = [float(v) for v in self._lammps.readline().split()]
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

        super(LAMMPS, self).finalize()

    def parse_first_step(self, aliases):
        self._lammps = open(self.configuration["trajectory_file"]["value"], "r")

        self._itemsPosition = collections.OrderedDict()

        comp = -1

        while True:
            line = self._lammps.readline()
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
                    temp = self._lammps.readline().split()
                    idx = int(temp[self._id]) - 1
                    ty = int(temp[self._type]) - 1
                    label = str(self._lammpsConfig["elements"][ty][0])
                    mass = str(self._lammpsConfig["elements"][ty][1])
                    name = "{:s}_{:d}".format(
                        str(self._lammpsConfig["elements"][ty][0]), idx
                    )
                    self._rankToName[int(temp[0]) - 1] = name
                    g.add_node(idx, label=label, mass=mass, atomName=name)

                if self._lammpsConfig["n_bonds"] is not None:
                    for idx1, idx2 in self._lammpsConfig["bonds"]:
                        g.add_link(idx1, idx2)

                self._chemicalSystem = ChemicalSystem()

                for cluster in g.build_connected_components():
                    if len(cluster) == 1:
                        node = cluster.pop()
                        try:
                            element = get_element_from_mapping(
                                aliases, node.label, mass=node.mass
                            )
                            obj = Atom(symbol=element, name=node.atomName)
                        except TypeError:
                            print("EXCEPTION in LAMMPS loader")
                            print(f"node.element = {node.element}")
                            print(f"node.atomName = {node.atomName}")
                            print(f"rankToName = {self._rankToName}")
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

                    self._chemicalSystem.add_chemical_entity(obj)
                self._last = comp + self._nAtoms + 1

                break

            elif line.startswith("ITEM: NUMBER OF ATOMS"):
                self._nAtoms = int(self._lammps.readline())
                comp += 1
                continue
