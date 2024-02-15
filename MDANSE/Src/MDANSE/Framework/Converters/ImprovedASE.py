# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/ASEConverter.py
# @brief     Implements a general-purpose loader based on ASE
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import re
from os.path import expanduser

from ase.io import iread, read
from ase.atoms import Atoms as ASEAtoms
from ase.io.trajectory import Trajectory as ASETrajectory
import numpy as np
import h5py


from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter, InteractiveConverter
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Graph import Graph
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    PeriodicRealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class ASETrajectoryFileError(Error):
    pass


class ImprovedASE(Converter):
    """
    Converts any trajectory to a HDF trajectory using the ASE io module.
    """

    label = "ImprovedASE"

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
            frame = read(self.configuration["trajectory_file"]["value"], index=index)
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

        # Close the output trajectory.
        self._trajectory.close()

        super(ImprovedASE, self).finalize()

    def parse_first_step(self):
        try:
            self._input = ASETrajectory(self.configuration["trajectory_file"]["value"])
        except:
            self._input = iread(
                self.configuration["trajectory_file"]["value"], index="[:]"
            )
            first_frame = read(self.configuration["trajectory_file"]["value"], index=0)
            last_iterator = 0
            generator = iread(self.configuration["trajectory_file"]["value"])
            for _ in generator:
                last_iterator += 1
            generator.close()
            self._total_number_of_steps = last_iterator
        else:
            first_frame = self._input[0]
            self._total_number_of_steps = len(self._input)

        self._timeaxis = self._timestep * np.arange(self._total_number_of_steps)

        self._fractionalCoordinates = np.all(first_frame.get_pbc())

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
                name = "".join(["{:s}{:d}".format(k, v) for k, v in sorted(c.items())])
                obj = AtomCluster(name, atList)

            self._chemicalSystem.add_chemical_entity(obj)

