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
from __future__ import annotations

import collections

import numpy as np

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class CellFileError(Error):
    pass


class CellFile(dict):
    """Opens and reads the CP2K cell file.

    The CP2K cell output contains the unit cell size for each simulation step.
    """

    def __init__(self, filename):
        self["instance"] = open(filename, encoding="utf-8")

        # Skip the first line
        self["instance"].readline()

        contents = self["instance"].readlines()
        if not contents:
            raise CellFileError("No cell contents found in the cell file")

        self["n_frames"] = len(contents)

        time_steps = []
        self["cells"] = []
        for line in contents:
            words = line.strip().split()

            if len(words) != 12:
                raise CellFileError(f"Invalid format for cell line: {line}")

            try:
                time_steps.append(float(words[1]))
            except ValueError:
                raise CellFileError(
                    f"Cannot cast time step {words[1]} to a floating point number"
                )

            try:
                cell = np.array(words[2:11], dtype=np.float64).reshape((3, 3))
            except ValueError:
                raise CellFileError(
                    f"Cannot cast cell coordinates {words[2:11]} to floating point numbers"
                )

            self["cells"].append(cell)

        if len(time_steps) == 1:
            self["time_step"] = 0.0
        else:
            self["time_step"] = time_steps[1] - time_steps[0]

    def read_step(self, step: int):
        """Reads and returns the unit cell constants at the requested
        simulation step (frame)

        Arguments:
            step -- number of the simulation frame to be read

        Raises:
            CellFileError: if the frame with the number *step* cannot be read

        Returns:
            ndarray -- a (3,3) array of unit cell constants
        """

        if step < 0 or step >= self["n_frames"]:
            raise CellFileError("Invalid step number")

        return self["cells"][step]

    def close(self):
        """Closes the file that was, until now, open for reading."""
        self["instance"].close()


class CP2KConverterError(Error):
    pass


class CP2K(Converter):
    """Converts a CP2K trajectory to an MDT trajectory."""

    label = "CP2K"

    settings = collections.OrderedDict()
    settings["pos_file"] = (
        "XYZFileConfigurator",
        {
            "wildcard": "XYZ files (*.xyz);;All files (*)",
            "default": "INPUT_FILENAME.xyz",
            "label": "Positions file (XYZ)",
        },
    )
    settings["vel_file"] = (
        "OptionalXYZFileConfigurator",
        {
            "wildcard": "XYZ files (*.xyz);;All files (*)",
            "default": "",
            "label": "Velocity file (XYZ, optional)",
        },
    )
    settings["force_file"] = (
        "OptionalXYZFileConfigurator",
        {
            "wildcard": "XYZ files (*.xyz);;All files (*)",
            "default": "",
            "label": "Force file (XYZ, optional)",
        },
    )
    settings["cell_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "Cell files (*.cell);;All files (*)",
            "default": "INPUT_FILENAME.cell",
            "label": "CP2K unit cell file (.cell)",
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "pos_file"},
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "pos_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        Opens the input files and checks them for consistency.
        """
        super().initialize()

        self._atomicAliases = self.configuration["atom_aliases"]["value"]
        self._xyzFile = self.configuration["pos_file"]

        if self.configuration["vel_file"]["value"]:
            self._velFile = self.configuration["vel_file"]
            if abs(self._xyzFile["time_step"] - self._velFile["time_step"]) > 1.0e-09:
                raise CP2KConverterError(
                    "Inconsistent time step between pos and vel files"
                )

            if self._xyzFile["n_frames"] != self._velFile["n_frames"]:
                raise CP2KConverterError(
                    "Inconsistent number of frames between pos and vel files"
                )

        if self.configuration["force_file"]["value"]:
            self._forceFile = self.configuration["force_file"]
            if abs(self._xyzFile["time_step"] - self._forceFile["time_step"]) > 1.0e-09:
                raise CP2KConverterError(
                    "Inconsistent time step between pos and force files"
                )

            if self._xyzFile["n_frames"] != self._forceFile["n_frames"]:
                raise CP2KConverterError(
                    "Inconsistent number of frames between pos and force files"
                )

        self._cellFile = CellFile(self.configuration["cell_file"]["filename"])

        if abs(self._cellFile["time_step"] - self._xyzFile["time_step"]) > 1.0e-09:
            LOG.error(f"{self._cellFile['time_step']}, {self._xyzFile['time_step']}")
            raise CP2KConverterError(
                "Inconsistent time step between pos and cell files"
            )

        if self._cellFile["n_frames"] != self._xyzFile["n_frames"]:
            raise CP2KConverterError(
                "Inconsistent number of frames between pos and cell files"
            )

        # The number of steps of the analysis.
        self.numberOfSteps = self._xyzFile["n_frames"]

        self._chemical_system = ChemicalSystem()
        element_list = []

        for _, symbol in enumerate(self._xyzFile["atoms"]):
            element = get_element_from_mapping(self._atomicAliases, symbol)
            element_list.append(element)

        self._chemical_system.initialise_atoms(element_list)

        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
        )

        data_to_be_written = ["configuration", "time"]
        if self.configuration["vel_file"]["value"]:
            data_to_be_written.append("velocities")
        if self.configuration["force_file"]["value"]:
            data_to_be_written.append("forces")

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop not the index of the frame.
        """

        # Read the current coordinates in the XYZ file.
        coords = self._xyzFile.read_step(index) * measure(1.0, iunit="ang").toval("nm")

        unitcell = UnitCell(
            self._cellFile.read_step(index) * measure(1.0, iunit="ang").toval("nm")
        )

        variables = {}
        if self.configuration["vel_file"]["value"]:
            variables["velocities"] = self._velFile.read_step(index) * measure(
                1.0, iunit="ang/fs"
            ).toval("nm/ps")
        if self.configuration["force_file"]["value"]:
            variables["forces"] = self._forceFile.read_step(index) * measure(
                1.0, iunit="Da ang / fs2"
            ).toval("Da nm / ps2")

        real_conf = PeriodicRealConfiguration(
            self._trajectory.chemical_system, coords, unitcell, **variables
        )

        if self._configuration["fold"]["value"]:
            real_conf.fold_coordinates()

        time = index * self._xyzFile["time_step"] * measure(1.0, iunit="fs").toval("ps")

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            real_conf,
            time,
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
                "velocities": "nm/ps",
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
        Closes the files and calls the
        superclass finalize method.
        """

        self._xyzFile.close()

        if self.configuration["vel_file"]["value"]:
            self._velFile.close()

        if self.configuration["force_file"]["value"]:
            self._forceFile.close()

        self._cellFile.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
