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
from more_itertools import ilen

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parameters import (
    AtomMapping,
    Boolean,
    OutputTrajectory,
    PathParam,
    to_class,
)
from MDANSE.Framework.Parsers import CASTEPMDFile
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class CASTEP(Converter):
    """Converts a Castep Trajectory into an MDT trajectory file."""

    label = "CASTEP"

    trajectory_file = PathParam[CASTEPMDFile](
        mode="r",
        extensions={"MD files": "*.md"},
        label="A CASTEP MD trajectory file.",
        on_set=to_class(CASTEPMDFile),
    )
    atom_aliases = AtomMapping(
        depends={"trajectory": "trajectory_file"},
        label="Atom mapping",
    )
    fold = Boolean(label="Fold coordinates into box")
    output_files = OutputTrajectory()

    enabled = True

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()
        self._atomicAliases = self.atom_aliases
        self._frames = self.trajectory_file.frames

        # Save the number of steps
        self.numberOfSteps = ilen(self.trajectory_file.frames)

        # Create a bound universe
        self._chemical_system = ChemicalSystem()

        element_list = [
            get_element_from_mapping(self.atom_aliases, symbol)
            for symbol in self.trajectory_file.element_list
        ]

        self._chemical_system.initialise_atoms(element_list)

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.output_files.path,
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.output_files.dtype,
            chunking_limit=self.output_files.chunk_size,
            compression=self.output_files.compression,
        )

    def run_step(self, index: int) -> tuple[int, None]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            Index of the loop.

        Returns
        -------
        tuple[int, None]
        """
        frame = next(self._frames)

        # Read the information in the frame
        time_step = frame["time"]

        unit_cell = UnitCell(np.vstack(frame["h"]))
        coords = np.vstack(tuple(arr[1] for arr in frame["R"]))
        variables = {
            "velocities": np.vstack(tuple(arr[1] for arr in frame["V"])),
            "gradients": np.vstack(tuple(arr[1] for arr in frame["F"])),
        }

        conf = PeriodicRealConfiguration(
            self._trajectory.chemical_system, coords, unit_cell, **variables
        )

        if self.fold:
            conf.fold_coordinates()

        self._trajectory.dump_configuration(
            conf,
            time_step,
            units={
                "time": "ps",
                "coordinates": "nm",
                "unit_cell": "nm",
                "velocities": "nm/ps",
                "gradients": "Da nm/ps2",
            },
        )

        return index, None

    def combine(self, index, x):
        """Dummy combine step.

        Parameters
        ----------
        _index : int
            Unused.
        _x : None
            Unused.
        """

    def finalize(self):
        """
        Finalize the job.
        """
        self._frames.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
