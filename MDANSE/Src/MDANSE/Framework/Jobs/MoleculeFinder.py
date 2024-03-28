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

import numpy as np

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.TrajectoryUtils import brute_formula
from MDANSE.MolecularDynamics.Connectivity import Connectivity
from MDANSE.Chemistry.Structrures import MoleculeTester
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)


class MoleculeFinder(IJob):
    """
    Use this if your trajectory contains molecules, but MDANSE has not assigned
    labels to them. MoleculeFinder will output a new trajectory in which bond
    information is stored and groups of atoms connected by bonds are given labels
    which are either InChI strings or chemical formulae of the groups.
    </p>
    <b> THIS IS USABLE, BUT STILL AT AN EARLY STAGE AND NOT OPTIMISED </b>
    </p>
    Finds potential molecules in the trajectory, based on
    interatomic distances.
    </p>
    The tolerance is a fraction of expected bond length calculated from covalent radii.
    This means that a pair of C and H atoms will be considered as connected by a bond
    if they are at a distance smaller than (r_C + r_H) * (1 + tolerance).
    """

    label = "Molecule Finder"

    category = (
        "Analysis",
        "Trajectory",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["tolerance"] = (
        "FloatConfigurator",
        {"default": 0.25},
    )
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, -1, 1)},
    )
    settings["output_file"] = (
        "OutputTrajectoryConfigurator",
        {"format": "MDTFormat"},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration["frames"]["number"]
        self._input_trajectory = self.configuration["trajectory"]["instance"]
        self._tolerance = self.configuration["tolerance"]["value"]
        chemical_system = self._input_trajectory.chemical_system

        conn = Connectivity(trajectory=self._input_trajectory)
        conn.find_molecules(tolerance=self._tolerance)
        conn.add_bond_information()
        chemical_system.rebuild(conn._molecules)
        configuration = chemical_system.configuration
        coords = configuration.contiguous_configuration().coordinates
        for entity in chemical_system.chemical_entities:
            if entity.number_of_atoms > 1:
                moltester = MoleculeTester(entity, coords)
                inchistring = moltester.identify_molecule()
                if len(inchistring) > 0:
                    entity.name = inchistring
                else:
                    entity.name = brute_formula(entity)

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_file"]["dtype"],
            compression=self.configuration["output_file"]["compression"],
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. None
        """

        # get the Frame index
        frameIndex = self.configuration["frames"]["value"][index]

        n_coms = self._output_trajectory.chemical_system.number_of_atoms

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)
        conf = conf.contiguous_configuration()

        coords = conf.coordinates

        variables = {}
        if (
            "velocities"
            in self.configuration["trajectory"]["instance"]
            ._h5_file["configuration"]
            .keys()
        ):
            variables = {
                "velocities": self.configuration["trajectory"]["instance"]
                ._h5_file["/configuration/velocities"][frameIndex, :, :]
                .astype(np.float64)
            }

        if conf.is_periodic:
            com_conf = PeriodicRealConfiguration(
                self._output_trajectory.chemical_system,
                coords,
                conf.unit_cell,
                **variables,
            )
        else:
            com_conf = RealConfiguration(
                self._output_trajectory.chemical_system, coords, **variables
            )

        self._output_trajectory.chemical_system.configuration = com_conf

        # The times corresponding to the running index.
        time = self.configuration["frames"]["time"][index]

        self._output_trajectory.dump_configuration(time)

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

        # The input trajectory is closed.
        self.configuration["trajectory"]["instance"].close()

        # The output trajectory is closed.
        self._output_trajectory.close()
