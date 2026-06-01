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
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parameters import (
    AtomMapping,
    Boolean,
    OutputTrajectory,
    PathParam,
    to_class,
)
from MDANSE.Framework.Parsers import DLPField, DLPHistory
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class HistoryFileError(Exception):
    pass


class DL_POLYConverterError(Exception):
    pass


class DL_POLY(Converter):
    """Converts a DL_POLY trajectory to an MDT trajectory."""

    label = "DL-POLY"

    field_file = PathParam[DLPField](
        mode="r",
        extensions={"FIELD files": "FIELD*"},
        default="FIELD",
        label="Input FIELD file",
        on_set=to_class(DLPField),
    )
    history_file = PathParam[DLPHistory](
        mode="r",
        extensions={"HISTORY files": "HISTORY*"},
        default="HISTORY",
        label="Input HISTORY file",
        on_set=to_class(DLPHistory),
    )
    atom_aliases = AtomMapping(
        depends={"trajectory": "field_file"},
        label="Atom mapping",
        default={},
    )
    fold = Boolean(label="Fold coordinates into box")
    output_files = OutputTrajectory()

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self.frames = self.history_file.frames

        # The number of steps of the analysis.
        self.numberOfSteps = self.history_file.n_frames
        self._chemical_system = ChemicalSystem()

        self.field_file.build_chemical_system(self._chemical_system, self.atom_aliases)

        self._trajectory = TrajectoryWriter(
            self.output_files.path,
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.output_files.dtype,
            chunking_limit=self.output_files.chunk_size,
            compression=self.output_files.compression,
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

        if self.fold:
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
