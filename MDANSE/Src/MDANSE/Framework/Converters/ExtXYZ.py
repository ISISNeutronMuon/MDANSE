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

import numpy as np
from more_itertools import first, first_true

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Configurators import MultiFileWithAtomDataConfigurator
from MDANSE.Framework.Configurators.ExtXYZColumnMapConfigurator import Reference
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parsers.extxyz import ExtXYZFile
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    AbsoluteConfiguration,
    PeriodicAbsoluteConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell

try:
    import extxyz

    extxyz_available = True
except ImportError:
    extxyz_available = False


@IJob.register("ExtXYZ")
@Converter.register("ExtXYZ")
class ExtXYZ(Converter):
    """Converts a Castep Trajectory into an MDT trajectory file."""

    enabled = extxyz_available
    label = "ExtXYZ"
    requires_extras = ("extxyz",)

    settings = {}
    settings["xyz_file"] = (
        "MultiFileWithAtomDataConfigurator",
        {
            "wildcard": "XYZ files (*.xyz);;ExtXYZ files (*.extxyz);;All files (*)",
            "default": "INPUT_FILENAME.xyz",
            "label": "Input file",
            "parser": ExtXYZFile,
        },
    )
    settings["unit_cell"] = (
        "UnitCellConfigurator",
        {
            "label": "Unit cell if not in file.",
            "dependencies": {"trajectory": "xyz_file"},
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {
            "label": "Time step if not in file (assumed fs)",
            "default": 1.0,
            "mini": 1.0e-9,
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
    settings["column_mapping"] = (
        "ExtXYZColumnMapConfigurator",
        {
            "label": "Column mapping",
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
        self.trajectory_file: MultiFileWithAtomDataConfigurator = self.configuration[
            "xyz_file"
        ]
        self.frames = self.trajectory_file.frames

        self.column_mapping: dict[str, Reference | None] = self.configuration[
            "column_mapping"
        ].mapping
        self.units = self.configuration["column_mapping"].units

        # Save the number of steps
        self.numberOfSteps = self.trajectory_file.n_frames

        # Create a bound universe
        self._chemical_system = ChemicalSystem()

        spec_key = self.column_mapping["species"]

        element_list = [
            get_element_from_mapping(self.atom_aliases, symbol)
            for symbol in first(
                self.trajectory_file.parser_instances[spec_key.file].frames
            ).arrays[spec_key.key]
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
        frames = next(self.frames)

        # Read the information in the frame
        units = {
            "coords": measure(1.0, self.units["positions"]).toval("nm"),
            "velocities": measure(1.0, self.units["velocities"]).toval("nm / ps"),
            "masses": measure(1.0, self.units["masses"]).toval("Da"),
            "momenta": measure(1.0, self.units["momenta"]).toval("Da nm / ps"),
            "forces": measure(1.0, self.units["forces"]).toval("Da nm / ps2"),
            "unit_cell": measure(1.0, self.units["unit_cell"]).toval("nm"),
            "time": measure(1.0, self.units["time"]).toval("ps"),
        }

        match self.column_mapping.get("time"):
            case Reference(key=key, file=file, info=True):
                time_step = frames[file].info[key] * units["time"]
            case None:
                time_step = self.configuration["time_step"]["value"]
            case _:
                raise ValueError(
                    f"Unable to determine timestep from mapping: {self.column_mapping['time']}"
                )

        if (coord_key := self.column_mapping.get("positions")) is None:
            raise KeyError("Cannot determine positions key.")

        coords = frames[coord_key.file].arrays[coord_key.key] * units["coords"]

        variables = {}

        if vel_key := self.column_mapping.get("velocities"):
            variables["velocities"] = (
                frames[vel_key.file].arrays[vel_key.key] * units["velocities"]
            )
        elif (mom_key := self.column_mapping.get("momenta")) and (
            mass_key := self.column_mapping.get("masses")
        ):
            variables["velocities"] = (
                frames[mom_key.file].arrays[mom_key.key] * units["velocities"]
            ) / (
                frames[mass_key.file].arrays[mass_key.key][:, np.newaxis]
                * units["masses"]
            )
        elif mom_key := self.column_mapping.get("momenta"):
            variables["velocities"] = (
                frames[mom_key.file].arrays[mom_key.key]
                * units["velocities"]
                / np.array(self._chemical_system.atom_property("atomic_weight"))[
                    :, np.newaxis
                ]
            )

        if force_key := self.column_mapping.get("forces"):
            variables["gradients"] = (
                frames[force_key.file].arrays[force_key.key] * units["forces"]
            )

        if any(pbc for f in frames.values() for pbc in f.pbc):
            if self.configuration["unit_cell"]["apply"]:
                unit_cell = UnitCell(self.configuration["unit_cell"]["value"])
            else:
                cell = first(
                    f.cell
                    for f in frames.values()
                    if getattr(f, "cell", None) is not None
                )
                unit_cell = UnitCell(cell * units["unit_cell"])
            conf = PeriodicAbsoluteConfiguration(coords, unit_cell, **variables)
            if self.configuration["fold"]["value"]:
                conf.fold_coordinates()
        else:
            conf = AbsoluteConfiguration(coords, **variables)

        out_units = {
            "coordinates": "nm",
            "time": "ps",
            "unit_cell": "nm",
            "velocities": "nm / ps",
            "gradients": "Da nm / ps2",
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
