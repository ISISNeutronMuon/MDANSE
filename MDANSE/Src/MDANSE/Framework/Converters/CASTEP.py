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
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parsers import CASTEPMDFile
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class CASTEP(Converter):
    """Converts a Castep Trajectory into an MDT trajectory file."""

    label = "CASTEP"

    settings = collections.OrderedDict()
    settings["castep_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "MD files (*.md);;All files (*)",
            "default": "INPUT_FILENAME.md",
            "label": "Input MD file",
            "parser": CASTEPMDFile,
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "castep_file"},
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
            "root": "castep_file",
            "label": "MDANSE trajectory (filename, datatype, chunk size, compression, logfile output)",
        },
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.atom_aliases = self.configuration["atom_aliases"]["value"]

        # Create a representation of md file
        self.trajectory_file = self.configuration["castep_file"].instance
        self.frames = self.trajectory_file.frames

        # Save the number of steps
        self.numberOfSteps = self.trajectory_file.n_frames

        # Create a bound universe
        self._chemical_system = ChemicalSystem()

        element_list = [
            get_element_from_mapping(self.atom_aliases, symbol)
            for symbol in self.trajectory_file.element_list
        ]

        self._chemical_system.initialise_atoms(element_list)

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
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
        frame = next(self.frames)

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

        if self.configuration["fold"]["value"]:
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

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
