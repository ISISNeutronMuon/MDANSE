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
import re
from os.path import expanduser

from ase.io import iread, read
from ase.atoms import Atoms as ASEAtoms
from ase.io.trajectory import Trajectory as ASETrajectory
import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Graph import Graph
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    PeriodicRealConfiguration,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import elements_from_masses
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class ASETrajectoryFileError(Error):
    pass


class ImprovedASE(Converter):
    """
    Converts any trajectory to a HDF trajectory using the ASE io module.
    """

    label = "ImprovedASE"

    enabled = False

    settings = collections.OrderedDict()
    settings["trajectory_file"] = (
        "AseInputFileConfigurator",
        {
            "label": "Any MD trajectory file",
            "default": "INPUT_FILENAME.traj",
            "format": "guess",
        },
    )
    settings["configuration_file"] = (
        "AseInputFileConfigurator",
        {
            "label": "Any structure file supported by ASE",
            "optional": True,
            "default": "INPUT_FILENAME.any",
            "format": "guess",
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
    settings["elements_from_mass"] = (
        "BooleanConfigurator",
        {
            "label": "Try to determine chemical elements based on atom mass",
            "default": False,
        },
    )
    settings["mass_tolerance"] = (
        "FloatConfigurator",
        {
            "label": "allowed difference from database mass (in a.u.)",
            "default": 0.01,
            "mini": 1.0e-9,
        },
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
        self._chemicalSystem = None
        self._fractionalCoordinates = None
        self._nAtoms = None
        self._masses = None

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self._timestep = float(self.configuration["time_step"]["value"]) * measure(
            1.0, self.configuration["time_unit"]["value"]
        ).toval("ps")

        self.parse_first_step()
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
            frame = read(
                self.configuration["trajectory_file"]["value"],
                index=index,
                format=self.configuration["trajectory_file"]["format"],
            )
        time = self._timeaxis[index]

        unitCell = frame.cell.array

        unitCell *= measure(1.0, "ang").toval("nm")
        unitCell = UnitCell(unitCell)

        coords = frame.get_positions()
        coords *= measure(1.0, "ang").toval("nm")

        if self._fractionalCoordinates:
            conf = PeriodicBoxConfiguration(
                self._trajectory.chemical_system, coords, unitCell
            )
            realConf = conf.to_real_configuration()
        else:
            realConf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, coords, unitCell
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
        try:
            self._extra_input.close()
        except:
            pass
        # Close the output trajectory.
        self._trajectory.close()

        super(ImprovedASE, self).finalize()

    def extract_initial_information(self, ase_object):
        element_list = None

        if self._fractionalCoordinates is None:
            try:
                self._fractionalCoordinates = np.all(ase_object.get_pbc())
            except:
                pass

        if self._masses is None:
            try:
                self._masses = ase_object.get_masses()
            except:
                pass

        g = Graph()

        element_count = {}
        if self.configuration["elements_from_mass"]["value"]:
            tolerance = self.configuration["mass_tolerance"]["value"]
            if self._masses is None:
                return
            else:
                element_list = elements_from_masses(self._masses, tolerance=tolerance)
        else:
            try:
                element_list = ase_object.get_chemical_symbols()
            except:
                pass
        if element_list is None:
            return
        else:
            if self._nAtoms is None:
                self._nAtoms = len(element_list)
            if self._chemicalSystem is None:
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
                            print("EXCEPTION in ASE loader")
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
                        name = "".join(
                            ["{:s}{:d}".format(k, v) for k, v in sorted(c.items())]
                        )
                        obj = AtomCluster(name, atList)

                    self._chemicalSystem.add_chemical_entity(obj)

    def parse_optional_config(self):
        try:
            self._extra_input = read(
                self.configuration["configuration_file"]["value"],
                format=self.configuration["configuration_file"]["format"],
            )
        except FileNotFoundError:
            return
        except:
            for file_format in self.configuration[
                "configuration_file"
            ]._allowed_formats:
                try:
                    self._extra_input = read(
                        self.configuration["configuration_file"]["value"],
                        format=file_format,
                    )
                except:
                    continue
                else:
                    break
        else:
            self.extract_initial_information(self._extra_input)

    def parse_first_step(self):
        self.parse_optional_config()
        try:
            self._input = ASETrajectory(self.configuration["trajectory_file"]["value"])
        except:
            self._input = iread(
                self.configuration["trajectory_file"]["value"],
                index="[:]",
                format=self.configuration["trajectory_file"]["format"],
            )
            first_frame = read(
                self.configuration["trajectory_file"]["value"],
                index=0,
                format=self.configuration["trajectory_file"]["format"],
            )
            last_iterator = 0
            generator = iread(
                self.configuration["trajectory_file"]["value"],
                format=self.configuration["trajectory_file"]["format"],
            )
            for _ in generator:
                last_iterator += 1
            generator.close()
            self._total_number_of_steps = last_iterator
        else:
            first_frame = self._input[0]
            self._total_number_of_steps = len(self._input)
        self._timeaxis = self._timestep * np.arange(self._total_number_of_steps)

        self.extract_initial_information(first_frame)
