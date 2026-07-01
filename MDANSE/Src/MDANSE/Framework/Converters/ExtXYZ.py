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

import json
from collections.abc import Iterable
from functools import partial

from more_itertools import first_true

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parsers.extxyz import ExtXYZFile
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


@IJob.register("ExtXYZ")
@Converter.register("ExtXYZ")
class ExtXYZ(Converter):
    """Converts a Castep Trajectory into an MDT trajectory file."""

    label = "ExtXYZ"

    settings = {}
    settings["xyz_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "wildcard": "XYZ files (*.xyz);;ExtXYZ files (*.extxyz);;All files (*)",
            "default": "INPUT_FILENAME.xyz",
            "label": "Input file",
            "parser": ExtXYZFile,
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "xyz_file"},
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
            "root": "xyz_file",
        },
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.atom_aliases = self.configuration["atom_aliases"]["value"]

        # Create a representation of md file
        self.trajectory_file: ExtXYZFile = self.configuration["xyz_file"].instance
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
        time_step = frame.info["time"]

        def find_array_key(*trial: str) -> str | None:
            return first_true(trial, pred=frame.arrays.__contains__, default=None)

        coord_key = find_array_key("pos", "positions", "coords", "coordinates")

        if coord_key is None:
            raise KeyError("Cannot determine positions key.")

        coords = frame.arrays[coord_key]

        variables = {}
        if vel_key := find_array_key("velo", "velocity", "velocities"):
            variables["velocities"] = frame.arrays[vel_key]
        else:
            mom_key = find_array_key("momenta", "moment", "momentum")
            mass_key = find_array_key("mass", "masses")

            if all((mom_key, mass_key)):
                variables["velocities"] = frame.arrays[mom_key] / frame.arrays[mass_key]

        if force_key := find_array_key("force", "forces", "gradients", "grad"):
            variables["gradients"] = frame.arrays[force_key]

        if any(frame.pbc):
            unit_cell = UnitCell(frame.cell)
            conf = PeriodicRealConfiguration(
                self._trajectory.chemical_system, coords, unit_cell, **variables
            )
            if self.configuration["fold"]["value"]:
                conf.fold_coordinates()
        else:
            conf = RealConfiguration(
                self._trajectory.chemical_system, coords, **variables
            )

        if units := frame.info.get("units"):
            units = units.removeprefix("_JSON ")
            units = json.loads(units)
        else:
            units = {}

        length = units.get(coord_key, "nm")
        time = units.get("time", "fs")
        energy = units.get("energy", "eV")

        out_units = {
            "coordinates": length,
            "time": time,
            "unit_cell": units.get("unit_cell", length),
            "velocities": units.get(vel_key, f"{length}/{time}"),
            "gradients": units.get(force_key, f"{energy}/{length}"),
        }


        self._trajectory.dump_configuration(
            conf,
            time_step,
            units=out_units,
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
