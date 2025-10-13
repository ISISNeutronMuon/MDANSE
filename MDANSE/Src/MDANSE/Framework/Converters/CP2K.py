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
from typing import Any

import numpy as np
from more_itertools import all_equal

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parsers import CP2KCellFile, XYZFile
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class CP2KConverterError(Error):
    pass


class CP2K(Converter):
    """Converts a CP2K trajectory to an MDT trajectory."""

    UNITS = {
        "coordinates": measure(1.0, iunit="ang").toval("nm"),
        "cell": measure(1.0, iunit="ang").toval("nm"),
        "velocities": measure(1.0, iunit="ang/fs").toval("nm/ps"),
        "forces": measure(1.0, iunit="Da ang / fs2").toval("Da nm / ps2"),
        "time": measure(1.0, iunit="fs").toval("ps"),
    }

    label = "CP2K"

    settings = collections.OrderedDict()
    settings["pos_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "XYZ files (*.xyz);;All files (*)",
            "default": "INPUT_FILENAME.xyz",
            "label": "Positions file (XYZ)",
            "parser": XYZFile,
        },
    )
    settings["vel_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "XYZ files (*.xyz);;All files (*)",
            "default": "",
            "label": "Velocity file (XYZ, optional)",
            "parser": XYZFile,
            "optional": True,
        },
    )
    settings["force_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "XYZ files (*.xyz);;All files (*)",
            "default": "",
            "label": "Force file (XYZ, optional)",
            "parser": XYZFile,
            "optional": True,
        },
    )
    settings["cell_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "Cell files (*.cell);;All files (*)",
            "default": "INPUT_FILENAME.cell",
            "label": "CP2K unit cell file (.cell)",
            "parser": CP2KCellFile,
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
            "label": "MDANSE trajectory (filename, datatype, chunk size, compression, logfile output)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        Opens the input files and checks them for consistency.
        """
        super().initialize()

        self.files = {
            "coordinates": self.configuration["pos_file"].instance,
            "cell": self.configuration["cell_file"].instance,
        }

        if vfile := self.configuration["vel_file"].instance:
            self.files["velocities"] = vfile

        if ffile := self.configuration["force_file"].instance:
            self.files["forces"] = ffile

        for attr in ("time_step", "n_frames"):
            if not all_equal(getattr(file, attr) for file in self.files.values()):
                x = {name: getattr(file, attr) for name, file in self.files.items()}
                raise CP2KConverterError(f"Inconsistent {attr} between files: {x}")

        # The number of steps of the analysis.
        self.numberOfSteps = self.files["coordinates"].n_frames
        self.frames = {name: obj.frames for name, obj in self.files.items()}

        self._chemical_system = ChemicalSystem()

        element_list = [
            get_element_from_mapping(
                self.configuration["atom_aliases"]["value"], symbol
            )
            for symbol in self.files["coordinates"].atoms
        ]

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
        if "velocities" in self.files:
            data_to_be_written.append("velocities")
        if "forces" in self.files:
            data_to_be_written.append("forces")

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop not the index of the frame.
        """

        data = {
            key: next(frames) * self.UNITS[key] for key, frames in self.frames.items()
        }
        data["cell"] = UnitCell(data["cell"])

        real_conf = PeriodicRealConfiguration(
            self._trajectory.chemical_system,
            data.pop("coordinates"),
            data.pop("cell"),
            **data,
        )

        if self.configuration["fold"]["value"]:
            real_conf.fold_coordinates()

        time = index * self.files["coordinates"].time_step * self.UNITS["time"]

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

    def combine(self, _index: int, _x: Any) -> None:
        """
        Dummy combine as not needed.

        Parameters
        ----------
        _index : int
            Dummy index.
        _x :
            Dummy data.
        """
        pass

    def finalize(self):
        """
        Finalize the job.
        Closes the files and calls the
        superclass finalize method.
        """

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
