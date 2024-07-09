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

from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


_HISTORY_FORMAT = {}
_HISTORY_FORMAT["2"] = {
    "rec1": 81,
    "rec2": 31,
    "reci": 61,
    "recii": 37,
    "reciii": 37,
    "reciv": 37,
    "reca": 43,
    "recb": 37,
    "recc": 37,
    "recd": 37,
}
_HISTORY_FORMAT["3"] = {
    "rec1": 73,
    "rec2": 73,
    "reci": 73,
    "recii": 73,
    "reciii": 73,
    "reciv": 73,
    "reca": 73,
    "recb": 73,
    "recc": 73,
    "recd": 73,
}
_HISTORY_FORMAT["4"] = {
    "rec1": 73,
    "rec2": 73,
    "reci": 73,
    "recii": 73,
    "reciii": 73,
    "reciv": 73,
    "reca": 73,
    "recb": 73,
    "recc": 73,
    "recd": 73,
}


class HistoryFileError(Error):
    pass


class DL_POLYConverterError(Error):
    pass


class HistoryFile(dict):

    def __init__(self, filename):
        super().__init__()
        self["instance"] = open(filename, "rb")

        version = self.determine_version()
        self["version"] = version

        lenTestLine = len(self["instance"].readline())

        self["instance"].seek(0, 0)

        offset = lenTestLine - _HISTORY_FORMAT[self["version"]]["rec1"]

        self._headerSize = (
            _HISTORY_FORMAT[self["version"]]["rec1"]
            + _HISTORY_FORMAT[self["version"]]["rec2"]
            + 2 * offset
        )

        self["instance"].read(_HISTORY_FORMAT[self["version"]]["rec1"] + offset)

        data = self["instance"].read(_HISTORY_FORMAT[self["version"]]["rec2"] + offset)

        self["keytrj"], self["imcon"], self["natms"] = [
            int(v) for v in data.split()[0:3]
        ]

        if self["keytrj"] not in list(range(3)):
            raise HistoryFileError("Invalid value for trajectory output key.")

        if self["imcon"] not in list(range(4)):
            raise HistoryFileError(
                "Invalid value for periodic boundary conditions key."
            )

        if self["imcon"] == 0:
            self._configHeaderSize = _HISTORY_FORMAT[self["version"]]["reci"]
        else:
            self._configHeaderSize = (
                _HISTORY_FORMAT[self["version"]]["reci"]
                + 3 * _HISTORY_FORMAT[self["version"]]["recii"]
                + 4 * offset
            )

        self._configSize = (
            _HISTORY_FORMAT[self["version"]]["reca"]
            + offset
            + (self["keytrj"] + 1) * (_HISTORY_FORMAT[self["version"]]["recb"] + offset)
        ) * self["natms"]

        self._frameSize = self._configHeaderSize + self._configSize

        self["instance"].seek(0, 2)

        self["n_frames"] = (
            self["instance"].tell() - self._headerSize
        ) / self._frameSize

        self["instance"].seek(self._headerSize)

        data = self["instance"].read(self._configHeaderSize).splitlines()

        line = data[0].split()

        self._firstStep = int(line[1])

        self._timeStep = float(line[5])

        self._maskStep = 3 + 3 * (self["keytrj"] + 1) + 1

        if (self["version"] == "3") or (self["version"] == "4"):
            self._maskStep += 1

        self["instance"].seek(0)

    def read_step(self, step):
        self["instance"].seek(self._headerSize + step * self._frameSize)

        data = self["instance"].read(self._configHeaderSize).splitlines()

        line = data[0].split()
        currentStep = int(line[1])

        timeStep = (currentStep - self._firstStep) * self._timeStep
        if self["imcon"] > 0:
            cell = " ".join([i.decode("UTF-8") for i in data[1:]]).split()
            cell = np.array(cell, dtype=np.float64)
            cell = np.reshape(cell, (3, 3)).T
            cell *= measure(1.0, "ang").toval("nm")
        else:
            cell = None

        data = np.array(self["instance"].read(self._configSize).split())

        mask = np.ones((len(data),), dtype=bool)
        mask[0 :: self._maskStep] = False
        mask[1 :: self._maskStep] = False
        mask[2 :: self._maskStep] = False
        mask[3 :: self._maskStep] = False
        if (self["version"] == "3") or (self["version"] == "4"):
            mask[4 :: self._maskStep] = False

        config = np.array(np.compress(mask, data), dtype=np.float64)

        config = np.reshape(config, (self["natms"], 3 * (self["keytrj"] + 1)))

        config[:, 0:3] *= measure(1.0, "ang").toval("nm")

        # Case of the velocities
        if self["keytrj"] == 1:
            config[:, 3:6] *= measure(1.0, "ang/ps").toval("nm/ps")

        # Case of the velocities + gradients
        elif self["keytrj"] == 2:
            config[:, 3:6] *= measure(1.0, "ang/ps").toval("nm/ps")
            config[:, 6:9] *= measure(1.0, "uma ang / ps2").toval("uma nm / ps2")

        return timeStep, cell, config

    def close(self):
        self["instance"].close()

    def determine_version(self):
        """Determine the DL_POLY version from the history file based
        on record 1 and 2. See the DL_POLY 2, 3 and 4 manuals.

        Returns
        -------
        str
            The DL_POLY version.

        Raises
        ------
        HistoryFileError
            When the history file does not appear valid.
        """
        lines = self["instance"].readlines()
        self["instance"].seek(0, 0)
        record_1 = lines[0]
        record_2 = lines[1]
        if len(record_1) in [73, 74]:
            if len(record_2.split()) == 5:
                return "4"
            elif len(record_2.split()) == 3:
                return "3"
        elif len(record_1) in [81, 82]:
            return "2"

        raise HistoryFileError("Invalid DLPOLY history file")


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
    settings["output_file"] = (
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
        if self.configuration["output_file"]["write_logs"]:
            log_filename = self.configuration["output_file"]["root"] + ".log"
            self.add_log_file_handler(log_filename)

        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        self._fieldFile = self.configuration["field_file"]

        self._historyFile = HistoryFile(self.configuration["history_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = int(self._historyFile["n_frames"])

        self._chemicalSystem = ChemicalSystem()

        self._fieldFile.build_chemical_system(self._chemicalSystem, self._atomicAliases)

        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemicalSystem,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_file"]["dtype"],
            compression=self.configuration["output_file"]["compression"],
        )

        self._velocities = None

        self._gradients = None

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        # The x, y and z values of the current frame.
        time, unitCell, config = self._historyFile.read_step(index)

        unitCell = UnitCell(unitCell)

        if self._historyFile["imcon"] > 0:
            conf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, config[:, 0:3], unitCell
            )
        else:
            conf = RealConfiguration(self._trajectory.chemical_system, config[:, 0:3])

        if self.configuration["fold"]["value"]:
            conf.fold_coordinates()

        if self._velocities is not None:
            conf["velocities"] = config[:, 3:6]

        if self._gradients is not None:
            conf["gradients"] = config[:, 6:9]

        self._trajectory.chemical_system.configuration = conf

        self._trajectory.dump_configuration(
            time,
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
                "velocities": "nm/ps",
                "gradients": "uma nm/ps2",
            },
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

        self._historyFile.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(DL_POLY, self).finalize()
