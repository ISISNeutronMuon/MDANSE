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
from more_itertools import consume as drop

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parsers import DLPField, DLPHistory
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


class DL_POLY(Converter):
    """Converts a DL_POLY trajectory to an MDT trajectory."""

    label = "DL-POLY"

    settings = collections.OrderedDict()
    settings["field_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "FIELD files (FIELD*);;All files (*)",
            "default": "INPUT_FILENAME",
            "label": "Input FIELD file",
            "parser": DLPField,
        },
    )
    settings["history_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "HISTORY files (HISTORY*);;All files (*)",
            "default": "INPUT_FILENAME",
            "label": "Input HISTORY file",
            "parser": DLPHistory,
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

        self.field_file = self.configuration["field_file"].instance
        self.history_file = self.configuration["history_file"].instance
        self.frames = self.history_file.frames

        # The number of steps of the analysis.
        self.numberOfSteps = self.history_file.n_frames
        self._chemical_system = ChemicalSystem()

        self.field_file.build_chemical_system(
            self._chemical_system, self._atomicAliases
        )

        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
            initial_charges=self.field_file.get_atom_charges(),
        )

    def run_step(self, index: int) -> tuple[int, None]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            The index of the loop.

        Notes
        -----
        The argument index is note the index of the frame.
        the index of the step.

        Returns
        -------
        int
            Index.
        """

        frame = next(self.frames)

        if self.history_file.imcon:
            conf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, frame["positions"], frame["unit_cell"]
            )
        else:
            conf = RealConfiguration(
                self._trajectory.chemical_system, frame["positions"]
            )

        if self.configuration["fold"]["value"]:
            conf.fold_coordinates()

        if "velocities" in frame:
            conf["velocities"] = frame["velocities"]
        if "gradients" in frame:
            conf["gradients"] = frame["gradients"]

        self._trajectory.dump_configuration(
            conf,
            frame["time"],
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
                "velocities": "nm/ps",
                "gradients": "Da nm/ps2",
            },
        )

        self._trajectory.write_charges(frame["charge"], index)

        return index, None

    def combine(self, index: int, x: Any):
        """Join job steps.

        Parameters
        ----------
        index : int
            Current index.
        x : Any
            Misc data.
        """
        pass

    def finalize(self):
        """
        Finalize the job.
        """

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
