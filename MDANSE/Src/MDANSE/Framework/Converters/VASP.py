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
from functools import partial

from more_itertools import run_length

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parameters import (
    AtomMapping,
    Boolean,
    Float,
    OutputTrajectory,
    PathParam,
    to_class,
)
from MDANSE.Framework.Parsers import XDATCARFile
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import PeriodicBoxConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class VASPConverterError(Exception):
    pass


class VASP(Converter):
    """Converts a VASP XDATCAR file to an MDT trajectory.

    This converter works for XDATCAR files which contain a *header*
    specifying the unit cell size and atom types.

    If your XDATCAR file does not have a header, you can add it manually
    to the beginning of the file. The header can be copied from
    the CONTCAR file.

    A valid header should look like this:

    unknown system
           1
     9.050041    0.000000    0.000000
     0.000000    8.236754    0.000000
     0.000000    0.000000   11.000452
    Cu   Rb   Cl    S
    9   4   7   12

    where the last two lines specify the atomic types and the number
    of the atoms of each type in the same order as they appear in the
    atom coordinates below.
    """

    label = "VASP"

    trajectory_file = PathParam[XDATCARFile](
        mode="r",
        extensions={"XDATCAR input": "XDATCAR*"},
        label="Input XDATCAR file",
        on_set=to_class(XDATCARFile),
    )
    atom_aliases = AtomMapping(
        depends={"trajectory": "trajectory_file"},
        label="Atom mapping",
        default={},
    )
    time_step = Float(
        label="Time step (fs)",
        default=1.0,
        minimum=1e-9,
    )
    fold = Boolean(label="Fold coordinates into box")
    output_files = OutputTrajectory(
        label="MDANSE trajectory (filename, datatype, chunk size, compression, logfile output)",
    )

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self._atomicAliases = self.atom_aliases

        self.frames = self.trajectory_file.frames

        # The number of steps of the analysis.
        self.numberOfSteps = self.trajectory_file.n_frames

        self._chemical_system = ChemicalSystem()
        element_list = [
            get_element_from_mapping(self._atomicAliases, symbol)
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

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        frame = next(self.frames)

        # Read the current step in the xdatcar file.
        coords = frame["coords"]
        unitCell = frame["unit_cell"]

        conf = PeriodicBoxConfiguration(
            self._trajectory.chemical_system, coords, unitCell
        )

        # The coordinates in VASP are in box format. Convert them into real coordinates.
        real_conf = conf.to_real_configuration()

        if self.fold:
            # The real coordinates are folded then into the simulation box (-L/2,L/2).
            real_conf.fold_coordinates()

        # Compute the actual time
        time = frame["step"] * self.time_step * self.trajectory_file.UNIT_CONV["time"]

        # Dump the configuration to the output trajectory
        self._trajectory.dump_configuration(
            real_conf,
            time,
            units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
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

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
