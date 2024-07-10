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

from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.Framework.AtomMapping import get_element_from_mapping


HBAR = measure(1.05457182e-34, "kg m2 / s").toval("uma nm2 / ps")
HARTREE = measure(27.2113845, "eV").toval("uma nm2 / ps2")
BOHR = measure(5.29177210903e-11, "m").toval("nm")


class CASTEPError(Error):
    pass


class CASTEP(Converter):
    """
    Converts a Castep Trajectory into a HDF trajectory file.
    """

    label = "CASTEP"

    settings = collections.OrderedDict()
    settings["castep_file"] = (
        "MDFileConfigurator",
        {
            "wildcard": "MD files (*.md);;All files (*)",
            "default": "INPUT_FILENAME.md",
            "label": "Input MD file",
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
    settings["output_file"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "castep_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        if self.configuration["output_file"]["write_logs"]:
            log_filename = self.configuration["output_file"]["root"] + ".log"
            self.add_log_file_handler(log_filename, self.configuration["output_file"]["log_level"])

        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        # Create a representation of md file
        self._castepFile = self.configuration["castep_file"]

        # Save the number of steps
        self.numberOfSteps = self._castepFile["n_frames"]

        # Create a bound universe
        self._chemical_system = ChemicalSystem()

        # Populate the universe with atoms based on how many of each atom is in the read trajectory
        for symbol, number in self._castepFile["atoms"]:
            for i in range(number):
                element = get_element_from_mapping(self._atomicAliases, symbol)
                self._chemical_system.add_chemical_entity(
                    Atom(symbol=element, name="%s_%d" % (symbol, i))
                )

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_file"]["dtype"],
            compression=self.configuration["output_file"]["compression"],
        )

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        :return: The index of the step and None
        :rtype: (int, None)-tuple

        @note: the argument index is the index of the loop not the index of the frame.
        """

        # Retrieve the number of atoms
        nAtoms = self._castepFile["n_atoms"]

        # Read the informatino in the frame
        time_step, unit_cell, config = self._castepFile.read_step(index)

        coords = config[0:nAtoms, :]
        variables = {}
        variables["velocities"] = config[nAtoms : 2 * nAtoms, :]
        variables["gradients"] = config[2 * nAtoms : 3 * nAtoms, :]

        conf = PeriodicRealConfiguration(
            self._trajectory.chemical_system, coords, unit_cell, **variables
        )

        if self.configuration["fold"]["value"]:
            conf.fold_coordinates()

        self._trajectory.chemical_system.configuration = conf

        self._trajectory.dump_configuration(
            time_step,
            units={
                "time": "ps",
                "coordinates": "nm",
                "unit_cell": "nm",
                "velocities": "nm/ps",
                "gradients": "uma nm/ps2",
            },
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

        self._castepFile.close()  # Close the .md file.

        # Close the output trajectory.
        self._trajectory.close()

        super(CASTEP, self).finalize()
