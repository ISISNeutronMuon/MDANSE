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

from MDANSE.Core.Error import Error
from MDANSE.Extensions import xtc, trr
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class GromacsConverterError(Error):
    pass


class Gromacs(Converter):
    """
    Converts a Gromacs trajectory to a HDF trajectory.
    """

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
    settings["output_file"] = (
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
        if self.configuration["output_file"]["write_logs"]:
            log_filename = self.configuration["output_file"]["root"] + ".log"
            self.add_log_file_handler(
                log_filename, self.configuration["output_file"]["log_level"]
            )

        data_to_be_written = ["configuration", "time"]

        # Create XTC or TRR object depending on which kind of trajectory was loaded
        if self.configuration["xtc_file"]["filename"][-4:] == ".xtc":
            self._xdr_file = xtc.XTCTrajectoryFile(
                self.configuration["xtc_file"]["filename"], "r"
            )
            self._xtc = True
        elif self.configuration["xtc_file"]["filename"][-4:] == ".trr":
            self._xdr_file = trr.TRRTrajectoryFile(
                self.configuration["xtc_file"]["filename"], "r"
            )
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
            self._read_velocities, self._read_forces = bool(
                self._read_velocities
            ), bool(self._read_forces)

            if self._read_velocities:
                data_to_be_written.append("velocities")
            if self._read_forces:
                data_to_be_written.append("gradients")
        else:
            raise GromacsConverterError(
                "Invalid file format: Gromacs converter can only convert XTC and TRR files, "
                "but %s was provided." % self.configuration["xtc_file"]["filename"][-4:]
            )

        # The number of steps of the analysis.
        self.numberOfSteps = len(self._xdr_file)

        # Create all chemical entities from the PDB file.
        pdb_reader = PDBReader(self.configuration["pdb_file"]["filename"])
        chemical_system = pdb_reader.build_chemical_system()

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_file"]["dtype"],
            compression=self.configuration["output_file"]["compression"],
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
            coords, times, steps, box, __, velocities, forces = self._xdr_file.read(
                1, get_velocities=self._read_velocities, get_forces=self._read_forces
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

        self._trajectory.chemical_system.configuration = conf

        # The current time.
        time = times[0]

        self._trajectory.dump_configuration(time)

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
        self._trajectory.close()

        super(Gromacs, self).finalize()
