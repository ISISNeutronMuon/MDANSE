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

from MDANSE.Core.Error import Error
from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import PeriodicBoxConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.Framework.AtomMapping import get_element_from_mapping


class VASPConverterError(Error):
    pass


class VASP(Converter):
    """
    Converts a VASP trajectory to a HDF trajectory.
    """

    label = "VASP (>=5)"

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
    settings["output_file"] = (
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
        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        self._xdatcarFile = self.configuration["xdatcar_file"]

        # The number of steps of the analysis.
        self.numberOfSteps = int(self._xdatcarFile["n_frames"])

        self._chemicalSystem = ChemicalSystem()

        for symbol, number in self._xdatcarFile["atoms"]:
            for i in range(number):
                element = get_element_from_mapping(self._atomicAliases, symbol)
                self._chemicalSystem.add_chemical_entity(
                    Atom(symbol=element, name="{:s}_{:d}".format(symbol, i))
                )

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemicalSystem,
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

        # Bind the configuration to the chemcial system
        self._trajectory.chemical_system.configuration = real_conf

        # Compute the actual time
        time = (
            index
            * self.configuration["time_step"]["value"]
            * measure(1.0, "fs").toval("ps")
        )

        # Dump the configuration to the output trajectory
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
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
        self._trajectory.close()

        super(VASP, self).finalize()
