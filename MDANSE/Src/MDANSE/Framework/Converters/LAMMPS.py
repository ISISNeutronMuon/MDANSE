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
from MDANSE.Framework.Parameters import (
    AtomMapping,
    Boolean,
    Float,
    Integer,
    OutputTrajectory,
    PathParam,
    SingleChoice,
    to_class,
)
from MDANSE.Framework.Parsers import (
    LAMMPSConfigFile,
    LAMMPScustom,
    LAMMPSReader,
    LAMMPSxyz,
)
from MDANSE.Framework.Parsers.LAMMPS import LAMMPS_UNITS
from MDANSE.Framework.Parsers.LAMMPSConfig import ATOM_TYPES_MAP
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

if TYPE_CHECKING:
    from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem


class LAMMPS(Converter):
    """Converts a LAMMPS trajectory to an MDT trajectory."""

    label = "LAMMPS"

    _READERS = {
        "custom": LAMMPScustom,
        "xyz": LAMMPSxyz,
    }

    config_file = PathParam[LAMMPSConfigFile](
        mode="r",
        label="LAMMPS configuration file.",
        extensions={"LAMMPS config": "*.config"},
        default="INPUT_FILENAME.config",
        on_set=to_class(LAMMPSConfigFile),
    )
    trajectory_file = PathParam(
        mode="r",
        label="LAMMPS trajectory file.",
        extensions={
            "XYZ files": "*.xyz",
            "Dump files": "*.dump",
            "HDF5 files": "*.h5",
            "LAMMPS files": "*.lammps",
        },
        default="INPUT_FILENAME.lammps",
    )
    trajectory_format = SingleChoice(
        label="LAMMPS trajectory format",
        choices=("custom", "xyz"),
        default="custom",
    )
    lammps_units = SingleChoice(
        label="LAMMPS unit system",
        default="real",
        choices=LAMMPS_UNITS.keys() | {"From config"},
    )
    atom_type = SingleChoice(
        label="LAMMPS atom type",
        choices=ATOM_TYPES_MAP.keys() | {"From config"},
        default="From config",
    )
    atom_aliases = AtomMapping(
        depends={"trajectory": "config_file"},
        label="Atom mapping",
        default={},
    )
    time_step = Float(
        label="Time step (lammps units, depends on unit system)",
        default=1.0,
        minimum=1e-9,
    )
    n_steps = Integer(
        label="Number of time steps (0 for automatic detection)",
        default=0,
        minimum=0,
    )
    fold = Boolean(label="Fold coordinates into box")
    output_files = OutputTrajectory()

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        # The number of steps of the analysis.
        self.numberOfSteps = self.n_steps

        if self.lammps_units == "From config":
            if "units" not in self.config_file:
                raise KeyError("Units not found in lammps config")
            self.lammps_units = self.config_file["units"]

        self._reader = self.create_reader(self.trajectory_format)

        self._reader.set_units(self.lammps_units)
        self._chemical_system = self.parse_first_step(self.atom_aliases)
        self._chemical_system.find_clusters_from_bonds()

        if self.numberOfSteps == 0:
            self.numberOfSteps = self._reader.get_time_steps(self.trajectory_file)

        charges_single_cell = self.config_file["charges"]
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
            self.output_files.path,
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.output_files.dtype,
            chunking_limit=self.output_files.chunk_size,
            compression=self.output_files.compression,
            initial_charges=charges,
        )

        self._start = 0
        self._reader.open_file(self.trajectory_file)
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
            lammps_units=self.lammps_units,
            atom_type=self.atom_type,
            timestep=self.time_step,
            fold_coordinates=self.fold,
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

        self._reader.open_file(self.trajectory_file)
        chemical_system = self._reader.parse_first_step(aliases, self.config_file)
        self._reader.close()
        return chemical_system
