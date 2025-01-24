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

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class HistoryFileError(Error):
    pass


class DL_POLYConverterError(Error):
    pass


class HistoryFile(dict):
    def __init__(self, filename):
        super().__init__()
        self._dist_conversion = measure(1.0, "ang").toval("nm")
        self._vel_conversion = measure(1.0, "ang/ps").toval("nm/ps")
        self._grad_conversion = measure(1.0, "uma ang / ps2").toval("uma nm / ps2")
        with open(filename, "r") as source:
            _ = source.readline()
            tagline = source.readline()
            toks = tagline.split()
            self["keytrj"], self["imcon"], self["natms"] = [int(v) for v in toks[:3]]
            timeline = source.readline()
            toks = timeline.split()
            self._timeStep = float(toks[5])
            self._firstStep = int(toks[1])
        n_frames = 0
        with open(filename, "r") as source:
            for line in source:
                if "timestep" in line:
                    n_frames += 1
        self["n_frames"] = n_frames
        self["instance"] = open(filename, "r")
        for _ in range(2):
            self["instance"].readline()

    def read_step(self, step):
        headerline = self["instance"].readline()
        currentStep = int(headerline.split()[1])

        timeStep = (currentStep - self._firstStep) * self._timeStep
        if self["imcon"] > 0:
            cell_nums = []
            for _ in range(3):
                cell_nums.append(
                    [float(x) for x in self["instance"].readline().split()]
                )
            cell = np.array(cell_nums, dtype=np.float64)
            cell = np.reshape(cell, (3, 3)).T
            cell *= self._dist_conversion
        else:
            cell = None

        charges = np.empty(self["natms"])
        positions = np.empty((self["natms"], 3))
        lines_per_atom = 2
        if self["keytrj"] > 0:
            velocities = np.empty((self["natms"], 3))
            lines_per_atom = 3
        if self["keytrj"] > 1:
            gradients = np.empty((self["natms"], 3))
            lines_per_atom = 4

        for atom_num in range(self["natms"]):
            for line_num in range(lines_per_atom):
                toks = self["instance"].readline().split()
                if line_num == 0:
                    charges[atom_num] = float(toks[3])
                elif line_num == 1:
                    positions[atom_num] = [float(x) for x in toks]
                elif line_num == 2:
                    velocities[atom_num] = [float(x) for x in toks]
                elif line_num == 3:
                    gradients[atom_num] = [float(x) for x in toks]

        positions *= self._dist_conversion
        config = [positions]
        # Case of the velocities
        if self["keytrj"] > 0:
            velocities *= self._vel_conversion
            config.append(velocities)

        # Case of the velocities + gradients
        if self["keytrj"] > 1:
            gradients *= self._grad_conversion
            config.append(gradients)

        return timeStep, cell, config, charges

    def close(self):
        self["instance"].close()


class DL_POLY(Converter):
    """
    Converts a DL_POLY trajectory to a HDF trajectory.
    """

    label = "DL-POLY"

    settings = collections.OrderedDict()
    settings["field_file"] = (
        "FieldFileConfigurator",
        {
            "wildcard": "FIELD files (FIELD*);;All files (*)",
            "default": "INPUT_FILENAME",
            "label": "Input FIELD file",
        },
    )
    settings["history_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "HISTORY files (HISTORY*);;All files (*)",
            "default": "INPUT_FILENAME",
            "label": "Input HISTORY file",
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "field_file"},
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    # settings['output_files'] = ('output_files', {'formats':["HDFFormat"]})
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "history_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        self._fieldFile = self.configuration["field_file"]

        self._historyFile = HistoryFile(self.configuration["history_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = int(self._historyFile["n_frames"])

        self._chemical_system = ChemicalSystem()

        self._fieldFile.build_chemical_system(
            self._chemical_system, self._atomicAliases
        )

        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
            initial_charges=self._fieldFile.get_atom_charges(),
        )

        self._velocities = None
        self._gradients = None

        if self._historyFile["keytrj"] > 0:
            self._velocities = True
        if self._historyFile["keytrj"] > 1:
            self._gradients = True

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        # The x, y and z values of the current frame.
        time, unitCell, config, charge = self._historyFile.read_step(index)

        unitCell = UnitCell(unitCell)

        if self._historyFile["imcon"] > 0:
            conf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, config[0], unitCell
            )
        else:
            conf = RealConfiguration(self._trajectory.chemical_system, config[0])

        if self.configuration["fold"]["value"]:
            conf.fold_coordinates()

        if self._velocities is not None:
            conf["velocities"] = config[1]

        if self._gradients is not None:
            conf["gradients"] = config[2]

        self._trajectory.dump_configuration(
            conf,
            time,
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
                "velocities": "nm/ps",
                "gradients": "uma nm/ps2",
            },
        )

        self._trajectory.write_charges(charge, index)

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

        self._historyFile.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super(DL_POLY, self).finalize()
