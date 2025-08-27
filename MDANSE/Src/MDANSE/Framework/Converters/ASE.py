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
from contextlib import suppress
from math import sqrt

import numpy as np
from ase import Atoms
from ase.io import iread, read
from ase.io.trajectory import Trajectory as ASETrajectory
from more_itertools import ilen

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import INTERNAL_UNITS, UnitError, measure
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class ASETrajectoryFileError(Error):
    pass


class ASE(Converter):
    """Converts a trajectory to MDT format using ASE.

    Attempts to convert a trajectory file to MDANSE .mdt format (HDF5).
    The conversion is done using the ase.io module.
    It works both for the ASE's own .traj format, and for other formats
    supported by ASE.
    Please help the ASE format detection mechanism by using
    standard input file names.
    """

    category = ("Converters", "General")
    label = "ASE"

    settings = collections.OrderedDict()
    settings["trajectory_file"] = (
        "ASEFileConfigurator",
        {
            "label": "An MD trajectory file supported by ASE",
            "default": "INPUT_FILENAME",
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "trajectory_file"},
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {"label": "Time step", "default": 1.0, "mini": 1.0e-9},
    )
    settings["time_unit"] = (
        "SingleChoiceConfigurator",
        {"label": "Time step unit", "choices": ["fs", "ps", "ns"], "default": "fs"},
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
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "label": "MDANSE trajectory (filename, format)",
            "formats": ["MDTFormat"],
            "root": "trajectory_file",
        },
    )

    UNIT_CONV = {
        "energy": measure(1.0, "eV").toval("Da nm2 / ps2"),
        "forces": measure(1.0, "eV/ang").toval("Da nm / ps2"),
        "time": measure(1.0, "fs").toval("ps"),
        "velocities": measure(1.0, "ang/fs").toval("nm/ps"),
        "length": measure(1.0, "ang").toval("nm"),
    }

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self._isPeriodic = None
        self._backup_cell = None
        self._keep_running = True
        self._initial_masses = None
        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["n_steps"]["value"]

        self._timestep = float(self.configuration["time_step"]["value"]) * measure(
            1.0, self.configuration["time_unit"]["value"]
        ).toval("ps")

        self.parse_first_step(self._atomicAliases)
        LOG.info(f"isPeriodic after parse_first_step: {self._isPeriodic}")
        self._start = 0

        if self.numberOfSteps < 1:
            self.numberOfSteps = self._total_number_of_steps

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
            initial_charges=self._initial_charges,
        )

        LOG.info(f"total steps: {self.numberOfSteps}")

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """
        if not self._keep_running:
            LOG.warning(f"Skipping frame {index}")
            return index, None

        variables = {}

        try:
            frame = self._input[index]
        except TypeError:
            frame = next(self._input)
        else:
            LOG.info("ASE using the slower way")
            frame = read(self.configuration["trajectory_file"]["value"], index=index)

        assert isinstance(frame, Atoms)
        time = self._timeaxis[index]

        if self._isPeriodic:
            unitCell = frame.cell.array
            if np.allclose(unitCell, 0.0):
                LOG.warning(f"Using initial unit cell: {self._backup_cell}")
                unitCell = self._backup_cell * self.units["length"]
            else:
                LOG.info(f"Unit cell from frame: {unitCell}")
                unitCell *= self.units["length"]
            unitCell = UnitCell(unitCell)

        coords = frame.get_positions()
        coords *= self.units["length"]

        if (momenta := frame.arrays.get("momenta")) is not None:
            masses = (
                self._initial_masses.reshape((len(momenta), 1))
                if self._initial_masses is not None
                else np.array(
                    self._chemical_system.atom_property("atomic_weight")
                ).reshape((len(momenta), 1))
            )
            variables["velocities"] = (
                (momenta * self.units["momenta"]) / masses
                if "momenta" in self.units
                else (momenta / masses) * self.units["velocities"]
            )

        if self._isPeriodic:
            try:
                real_conf = PeriodicRealConfiguration(
                    self._trajectory.chemical_system, coords, unitCell, **variables
                )
            except ValueError:
                self._keep_running = False
                LOG.warning(
                    f"Could not create configuration for frame {index}. Will skip the rest"
                )
                return index, None
            if self._configuration["fold"]["value"]:
                real_conf.fold_coordinates()
        else:
            try:
                real_conf = RealConfiguration(
                    self._trajectory.chemical_system, coords, **variables
                )
            except ValueError:
                self._keep_running = False
                LOG.warning(
                    f"Could not create configuration for frame {index}. Will skip the rest"
                )
                return index, None

        # A snapshot is created out of the current configuration.
        self._trajectory.dump_configuration(
            real_conf,
            time,
            units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
        )

        try:
            charges = frame.arrays["charges"]
        except KeyError:
            try:
                charges = frame.get_initial_charges()
            except Exception:
                pass
            else:
                self._trajectory.write_charges(charges, index)
        else:
            self._trajectory.write_charges(charges, index)

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

        self._input.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()

    def parse_first_step(self, mapping):
        try:
            self._input = ASETrajectory(self.configuration["trajectory_file"]["value"])
        except Exception:
            first_frame = read(self.configuration["trajectory_file"]["value"], index=0)
            self._input = iread(
                self.configuration["trajectory_file"]["value"]  # , index="[:]"
            )
            self._total_number_of_steps = ilen(
                iread(self.configuration["trajectory_file"]["value"])
            )
            LOG.debug(f"Length found using last_iterator={self._total_number_of_steps}")
        else:
            first_frame = self._input[0]
            self._total_number_of_steps = len(self._input)
            LOG.debug(
                f"Length found using len(self._input)={self._total_number_of_steps}"
            )

        assert isinstance(first_frame, Atoms)

        unit_conv = {}
        if "units" in first_frame.info:
            for key, val in first_frame.info["units"].items():
                if (key, val) == ("momenta", "(eV*u)^0.5"):
                    unit_conv["momenta"] = sqrt(
                        measure(1.0, "eV Da").toval("Da2 nm2/ps2")
                    )

                if key not in INTERNAL_UNITS:
                    continue

                with suppress(UnitError, KeyError):
                    unit_conv[key] = measure(1.0, val).toval(INTERNAL_UNITS[key])
        self.units = collections.ChainMap(unit_conv, self.UNIT_CONV)

        self._timeaxis = self._timestep * np.arange(self._total_number_of_steps)

        if self._isPeriodic is None:
            self._isPeriodic = np.all(first_frame.get_pbc())

        LOG.info("PBC in first frame = %s", first_frame.get_pbc())

        if self._isPeriodic:
            self._backup_cell = first_frame.cell.array

        LOG.info(
            "The following arrays were found in the trajectory: %s",
            ", ".join(first_frame.arrays),
        )

        self._initial_masses = first_frame.arrays.get("masses")
        self._initial_charges = first_frame.arrays.get("charges")

        if self._initial_charges is None:
            LOG.warning("ASE converter could not read partial charges from file.")

        element_list = first_frame.get_chemical_symbols()

        self._nAtoms = len(element_list)

        self._chemical_system = ChemicalSystem()
        self._chemical_system.initialise_atoms(element_list)
