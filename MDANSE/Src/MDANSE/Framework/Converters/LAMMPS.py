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

from typing import TYPE_CHECKING, Any, Literal

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Parsers import (
    LAMMPSConfigFile,
    LAMMPScustom,
    LAMMPSReader,
    LAMMPSxyz,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.ConfigFileConfigurator import (
        ConfigFileConfigurator,
    )


class LAMMPS(Converter):
    """Converts a LAMMPS trajectory to an MDT trajectory."""

    label = "LAMMPS"

    _READERS = {
        "custom": LAMMPScustom,
        "xyz": LAMMPSxyz,
    }

    settings = {}
    settings["config_file"] = (
        "FileWithAtomDataConfigurator",
        {
            "label": "LAMMPS configuration file",
            "wildcard": "All files (*);;Config files (*.config)",
            "default": "INPUT_FILENAME.config",
            "parser": LAMMPSConfigFile,
        },
    )
    settings["trajectory_file"] = (
        "InputFileConfigurator",
        {
            "label": "LAMMPS trajectory file",
            "wildcard": "All files (*);;XYZ files (*.xyz);;H5MD files (*.h5);;lammps files (*.lammps)",
            "default": "INPUT_FILENAME.lammps",
        },
    )
    settings["trajectory_format"] = (
        "SingleChoiceConfigurator",
        {
            "label": "LAMMPS trajectory format",
            "choices": ["custom", "xyz"],
            "default": "custom",
        },
    )
    settings["lammps_units"] = (
        "SingleChoiceConfigurator",
        {
            "label": "LAMMPS unit system",
            "choices": [
                "From config",
                "real",
                "metal",
                "si",
                "cgs",
                "electron",
                "micro",
                "nano",
            ],
            "default": "real",
        },
    )
    settings["atom_type"] = (
        "SingleChoiceConfigurator",
        {
            "label": "LAMMPS atom type",
            "choices": [
                "From config",
                "angle",
                "atomic",
                "body",
                "bond",
                "bpm/sphere",
                "charge",
                "dielectric",
                "dipole",
                "dpd",
                "edpd",
                "electron",
                "ellipsoid",
                "full",
                "hybrid",
                "line",
                "mdpd",
                "molecular",
                "peri",
                "rheo",
                "rheo/thermal",
                "smd",
                "sph",
                "sphere",
                "spin",
                "tdpd",
                "template",
                "tri",
                "wavepacket",
            ],
            "default": "From config",
        },
    )

    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "config_file"},
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {
            "label": "Time step (lammps units, depends on unit system)",
            "default": 1.0,
            "mini": 1.0e-9,
        },
    )
    settings["n_steps"] = (
        "IntegerConfigurator",
        {
            "label": "Number of time steps (0 for automatic detection)",
            "default": 0,
            "mini": 0,
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates in to box"},
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "config_file",
            "label": "MDANSE trajectory (filename, datatype, chunk size, compression, logfile output)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self._lammpsConfig = self.configuration["config_file"].instance

        self._lammps_units = self.configuration["lammps_units"]["value"]
        self._atom_type = self.configuration["atom_type"]["value"]

        if self._lammps_units == "From config":
            if "units" not in self._lammpsConfig:
                raise KeyError("Units not found in lammps config")
            self._lammps_units = self._lammpsConfig["units"]

        self._lammps_format = self.configuration["trajectory_format"]["value"]

        self._reader = self.create_reader(self._lammps_format)

        self._reader.set_units(self._lammps_units)
        self._chemical_system = self.parse_first_step(self._atomicAliases)
        self._chemical_system.find_clusters_from_bonds()

        if self.numberOfSteps == 0:
            self.numberOfSteps = self._reader.get_time_steps(
                self.configuration["trajectory_file"]["value"]
            )

        charges_single_cell = self._lammpsConfig["charges"]
        charges_single_cell *= self._reader.units["charge_conv"]

        # Assume replicate
        if len(charges_single_cell) < self._chemical_system.number_of_atoms:
            charges = list(charges_single_cell) * int(
                self._chemical_system.number_of_atoms // len(charges_single_cell)
            )
        else:
            charges = list(charges_single_cell)

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
            initial_charges=charges,
        )

        self._start = 0
        self._reader.open_file(self.configuration["trajectory_file"]["value"])
        self._reader.set_output(self._trajectory)

    def create_reader(self, trajectory_type: Literal["custom", "xyz"]) -> LAMMPSReader:
        """Create the required reader.

        Parameters
        ----------
        trajectory_type : Literal["custom", "xyz"]
            Type of file to load.

        Returns
        -------
        LAMMPSReader
            Configured reader.
        """
        return self._READERS[trajectory_type](
            lammps_units=self._lammps_units,
            atom_type=self._atom_type,
            timestep=self.configuration["time_step"]["value"],
            fold_coordinates=self.configuration["fold"]["value"],
        )

    def run_step(self, index) -> tuple[int, None]:
        """Runs a single step of the job.

        Parameters
        ----------
        index : int.
            The index of the step.

        Returns
        -------
        int
            Index of job step.
        """

        val1, val2 = self._reader.run_step(index)

        self._start = val2

        return val1, None

    def combine(self, index: int, x: Any) -> None:
        """No work to be done.

        Parameters
        ----------
        index : int.
            The index of the step.
        x : Any
            Data.
        """

    def finalize(self) -> None:
        """
        Finalize the job.
        """

        self._reader.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()

    def parse_first_step(self, aliases: dict[str, dict[str, str]]) -> ChemicalSystem:
        """Wrapper for `parse_first_step` on readers.

        Parameters
        ----------
        aliases : dict[str, dict[str, str]]
            Mapping of atomic aliases to elements.

        Returns
        -------
        ChemicalSystem
            Initialised structure.

        See Also
        --------
        LAMMPScustom.parse_first_step
        LAMMPSxyz.parse_first_step
        """

        self._reader.open_file(self.configuration["trajectory_file"]["value"])
        chemical_system = self._reader.parse_first_step(aliases, self._lammpsConfig)
        self._reader.close()
        return chemical_system
