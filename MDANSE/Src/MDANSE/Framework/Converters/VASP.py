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

from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import get_element_from_mapping
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import PeriodicBoxConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class VASPConverterError(Error):
    pass


class VASP(Converter):
    """Converts a VASP XDATCAR file to an MDT trajectory.

    This converter works for XDATCAR files which contain a *header*
    specifying the unit cell size and atom types.

    If your XDATCAR file does not have a header, you can add it manually
    to the beginning of the file. The header can be copied from
    the CONTCAR file.

    A valid header should look like this:

    unknown system
           1
     9.050041    0.000000    0.000000
     0.000000    8.236754    0.000000
     0.000000    0.000000   11.000452
    Cu   Rb   Cl    S
    9   4   7   12

    where the last two lines specify the atomic types and the number
    of the atoms of each type in the same order as they appear in the
    atom coordinates below.
    """

    label = "VASP"

    settings = collections.OrderedDict()
    settings["xdatcar_file"] = (
        "XDATCARFileConfigurator",
        {
            "wildcard": "XDATCAR files (XDATCAR*);;All files (*)",
            "default": "INPUT_FILENAME",
            "label": "Input XDATCAR file",
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "xdatcar_file"},
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {"label": "Time step (fs)", "default": 1.0, "mini": 1.0e-9},
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "xdatcar_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        self._xdatcarFile = self.configuration["xdatcar_file"]

        # The number of steps of the analysis.
        self.numberOfSteps = int(self._xdatcarFile["n_frames"])

        self._chemical_system = ChemicalSystem()
        element_list = []

        for symbol, number in zip(
            self._xdatcarFile["atoms"], self._xdatcarFile["atom_numbers"]
        ):
            for i in range(number):
                element = get_element_from_mapping(self._atomicAliases, symbol)
                element_list.append(element)
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

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        # Read the current step in the xdatcar file.
        coords = self._xdatcarFile.read_step(index)

        unitCell = UnitCell(self._xdatcarFile["cell_shape"])

        conf = PeriodicBoxConfiguration(
            self._trajectory.chemical_system, coords, unitCell
        )

        # The coordinates in VASP are in box format. Convert them into real coordinates.
        real_conf = conf.to_real_configuration()

        if self.configuration["fold"]["value"]:
            # The real coordinates are folded then into the simulation box (-L/2,L/2).
            real_conf.fold_coordinates()

        # Compute the actual time
        time = (
            self._xdatcarFile["step_number"]
            * self.configuration["time_step"]["value"]
            * measure(1.0, "fs").toval("ps")
        )

        # Dump the configuration to the output trajectory
        self._trajectory.dump_configuration(
            real_conf,
            time,
            units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"},
        )

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

        self._xdatcarFile.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
