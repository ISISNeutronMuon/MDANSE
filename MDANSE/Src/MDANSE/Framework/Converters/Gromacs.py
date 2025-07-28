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
from pathlib import Path

import numpy as np
from mdtraj.formats.trr import TRRTrajectoryFile
from mdtraj.formats.xtc import XTCTrajectoryFile

from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.IO.MinimalPDBReader import MinimalPDBReader
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class GromacsConverterError(Error):
    pass


class Gromacs(Converter):
    """Converts a Gromacs trajectory to an MDT trajectory."""

    label = "Gromacs"

    settings = collections.OrderedDict()
    settings["pdb_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "PDB files (*.pdb);;All files (*)",
            "default": "INPUT_FILENAME.pdb",
            "label": "Input PDB file",
        },
    )
    settings["xtc_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "XTC files (*.xtc);;TRR files (*.trr);;All files (*)",
            "default": "INPUT_FILENAME.xtc",
            "label": "xtc or trr file",
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
            "root": "pdb_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        data_to_be_written = ["configuration", "time"]

        filename = Path(self.configuration["xtc_file"]["filename"])
        # Create XTC or TRR object depending on which kind of trajectory was loaded
        if filename.suffix == ".xtc":
            self._xdr_file = XTCTrajectoryFile(bytes(filename), "r")
            self._xtc = True
        elif filename.suffix == ".trr":
            self._xdr_file = TRRTrajectoryFile(bytes(filename), "r")
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
                    )

            # The TRRTrajectoryFile object returns ints for these values, so turn them into bools
            self._read_velocities, self._read_forces = (
                bool(self._read_velocities),
                bool(self._read_forces),
            )

            if self._read_velocities:
                data_to_be_written.append("velocities")
            if self._read_forces:
                data_to_be_written.append("gradients")
        else:
            raise GromacsConverterError(
                "Invalid file format: Gromacs converter can only convert XTC and TRR files, "
                f"but {self.configuration['xtc_file']['filename'][-4:]} was provided."
            )

        # The number of steps of the analysis.
        self.numberOfSteps = len(self._xdr_file)

        # Create all chemical entities from the PDB file.
        pdb_reader = MinimalPDBReader(self.configuration["pdb_file"]["filename"])
        chemical_system = pdb_reader._chemical_system

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
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
            coords, times, steps, box = self._xdr_file.read(1)
        else:
            coords, times, steps, box, __, velocities, forces = self._xdr_file._read(
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

        if self.configuration["fold"]["value"]:
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
