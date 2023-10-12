# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Temperature.py
# @brief     Implements module/class/test Temperature
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np

from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.Connectivity import Connectivity
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)


class MoleculeFinder(IJob):
    """
    Computes the time-dependent temperature for a given trajectory.
        The temperature is determined from the kinetic energy i.e. the atomic velocities
        which are in turn calculated from the time-dependence of the atomic coordinates.
        Note that if the time step between frames saved in the trajectory is long (~ps)
        compared to the time step in the MD simulations (~fs) the
        velocities are averaged over many configurations and will not give accurate temperatures.
    """

    label = "Molecule Finder"

    category = (
        "Analysis",
        "Trajectory",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("hdf_trajectory", {})
    settings["frames"] = (
        "frames",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, -1, 1)},
    )
    settings["output_files"] = ("output_files", {"formats": ["hdf", "ascii"]})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration["frames"]["number"]
        self._input_trajectory = self.configuration["trajectory"]["hdf_trajectory"]
        chemical_system = self._input_trajectory.chemical_system

        conn = Connectivity(trajectory=self._input_trajectory)
        conn.find_molecules()
        conn.add_bond_information()
        chemical_system.rebuild(conn._molecules)

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_files"]["files"][0],
            chemical_system,
            self.numberOfSteps,
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


REGISTRY["molecule"] = MoleculeFinder
