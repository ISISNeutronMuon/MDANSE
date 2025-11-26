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

from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parsers import DCDFile, PDBFile
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

PI_2 = 0.5 * np.pi
RECSCALE32BIT = 1
RECSCALE64BIT = 2


@IJob.register("DCD")
@Converter.register("DCD")
class DCD(Converter):
    """Converts a DCD trajectory to an MDT trajectory."""

    label = "DCD"

    settings = {}
    settings["pdb_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "PDB files (*.pdb);;All files (*)",
            "default": "INPUT_FILENAME.pdb",
            "label": "Input PDB file",
            "parser": PDBFile,
        },
    )
    settings["dcd_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "DCD files (*.dcd);;All files (*)",
            "default": "INPUT_FILENAME.dcd",
            "label": "Input DCD file",
            "parser": DCDFile,
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "pdb_file"},
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {"default": 1.0, "label": "Time step (ps)"},
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
        },
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["dcd_file"].instance.n_frames

        self.frames = self.configuration["dcd_file"].instance.frames

        # Create all chemical entities from the PDB file.
        self._chemical_system = self.configuration[
            "pdb_file"
        ].instance.build_chemical_system(self.configuration["atom_aliases"]["value"])

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
        """

        # The x, y and z values of the current frame.
        unit_cell, config = next(self.frames)

        conf = PeriodicRealConfiguration(
            self._trajectory._chemical_system, config, unit_cell
        )

        if self.configuration["fold"]["value"]:
            conf.fold_coordinates()

        # The current time.
        time = index * self.configuration["time_step"]["value"]

        # Store a snapshot of the current configuration in the output trajectory.
        self._trajectory.dump_configuration(
            conf, time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
        )

        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
