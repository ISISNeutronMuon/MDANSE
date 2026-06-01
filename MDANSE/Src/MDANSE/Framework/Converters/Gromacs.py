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

import numpy as np
from mdtraj.formats.trr import TRRTrajectoryFile
from mdtraj.formats.xtc import XTCTrajectoryFile

from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parameters import (
    AtomMapping,
    Boolean,
    OutputTrajectory,
    PathParam,
    to_class,
)
from MDANSE.Framework.Parsers import PDBFile
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class GromacsConverterError(Exception):
    pass


class Gromacs(Converter):
    """Converts a Gromacs trajectory to an MDT trajectory."""

    label = "Gromacs"

    pdb_file = PathParam[PDBFile](
        mode="r",
        extensions={"PDB file": "*.pdb"},
        default="INPUT_FILENAME.pdb",
        label="Input PDB file.",
        on_set=to_class(PDBFile),
    )
    xtc_file = PathParam(
        mode="r",
        extensions={"XTC file": "*.xtc", "TRR file": "*.trr"},
        default="INPUT_FILENAME.xtc",
        label="Input XTC file.",
    )
    atom_aliases = AtomMapping(
        depends={"trajectory": "pdb_file"},
        label="Atom mapping",
        default={},
    )
    fold = Boolean(
        label="Fold coordinates into box",
    )
    output_files = OutputTrajectory()

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        data_to_be_written = ["configuration", "time"]

        if self.xtc_file.suffix not in {".xtc", ".trr"}:
            raise GromacsConverterError(
                "Invalid file format: Gromacs converter can only convert XTC and TRR files, "
                f"but {self.xtc_file.suffix} was provided."
            )

        # Create XTC or TRR object depending on which kind of trajectory was loaded
        if self.xtc_file.suffix == ".xtc":
            self._xdr_file = XTCTrajectoryFile(bytes(self.xtc_file), "r")
            self._xtc = True
        elif self.xtc_file.suffix == ".trr":
            self._xdr_file = TRRTrajectoryFile(bytes(self.xtc_file), "r")
            self._xtc = False

            # Extract information about whether velocities and forces are present in the TRR file
            try:
                self._read_velocities = self._xdr_file.has_velocities
                self._read_forces = self._xdr_file.has_forces
            except AttributeError:
                (
                    self._read_velocities,
                    self._read_forces,
                ) = self._xdr_file._check_has_velocities_forces()
                if self._read_velocities < 0 or self._read_forces < 0:
                    raise RuntimeError(
                        "Could not determine whether velocities or forces are present!"
                    ) from None

            # The TRRTrajectoryFile object returns ints for these values, so turn them into bools
            self._read_velocities, self._read_forces = (
                bool(self._read_velocities),
                bool(self._read_forces),
            )

            if self._read_velocities:
                data_to_be_written.append("velocities")
            if self._read_forces:
                data_to_be_written.append("gradients")

        # The number of steps of the analysis.
        self.numberOfSteps = len(self._xdr_file)

        # Create all chemical entities from the PDB file.
        chemical_system = self.pdb_file.build_chemical_system(self.atom_aliases)

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.output_files.path,
            chemical_system,
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

        variables = {}

        # The x, y and z values of the current frame.
        if self._xtc:
            coords, times, _steps, box = self._xdr_file.read(1)
        else:
            coords, times, _steps, box, __, velocities, forces = self._xdr_file._read(
                1,
                None,
                get_velocities=self._read_velocities,
                get_forces=self._read_forces,
            )

            if self._read_velocities:
                variables["velocities"] = velocities[0, :, :].astype(float)
            if self._read_forces:
                variables["gradients"] = forces[0, :, :].astype(float)

        coords = np.squeeze(coords)

        conf = PeriodicRealConfiguration(
            self._trajectory.chemical_system,
            coords,
            UnitCell(box[0, :, :]),
            **variables,
        )

        if self.fold:
            conf.fold_coordinates()

        # The current time.
        time = times[0]

        self._trajectory.dump_configuration(conf, time)

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

        self._xdr_file.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
