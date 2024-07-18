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
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Graph import Graph
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.MLogging import LOG


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
    settings["output_files"] = (
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
        super().initialize()

        self._isPeriodic = None
        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self._timestep = float(self.configuration["time_step"]["value"]) * measure(
            1.0, self.configuration["time_unit"]["value"]
        ).toval("ps")

        self.parse_first_step(self._atomicAliases)
        LOG.info(f"isPeriodic after parse_first_step: {self._isPeriodic}")
        self._start = 0

        if self.numberOfSteps < 1:
            self.numberOfSteps = self._total_number_of_steps

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemicalSystem,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            compression=self.configuration["output_files"]["compression"],
        )

        self._nameToIndex = dict(
            [(at.name, at.index) for at in self._trajectory.chemical_system.atom_list]
        )

        LOG.info(f"total steps: {self.numberOfSteps}")

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
            LOG.info("ASE using the slower way")
            frame = read(self.configuration["trajectory_file"]["value"], index=index)
        time = self._timeaxis[index]

        if self._isPeriodic:
            unitCell = frame.cell.array
            LOG.info(f"Unit cell from frame: {unitCell}")

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
        LOG.info(f"PBC in first frame = {first_frame.get_pbc()}")

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
                    LOG.error("EXCEPTION in ASE loader")
                    LOG.error(f"node.element = {node.element}")
                    LOG.error(f"node.atomName = {node.atomName}")
                    LOG.error(f"rankToName = {self._rankToName}")
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
