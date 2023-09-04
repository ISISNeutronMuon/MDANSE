# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Density.py
# @brief     Implements module/class/test Density
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from MDANSE import REGISTRY
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

NAVOGADRO = 6.02214129e23


class DensityError(Exception):
    pass


class Density(IJob):
    """
    Computes the atom and mass densities for a given trajectory. These are time dependent if the simulation box volume fluctuates.
    """

    label = "Density"

    category = (
        "Analysis",
        "Thermodynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("hdf_trajectory", {})
    settings["frames"] = ("frames", {"dependencies": {"trajectory": "trajectory"}})
    settings["output_files"] = ("output_files", {"formats": ["hdf", "netcdf", "ascii"]})
    settings["running_mode"] = ("running_mode", {})

    def initialize(self):
        self.numberOfSteps = self.configuration["frames"]["number"]

        self._n_frames = self.numberOfSteps

        self._n_atoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_atoms()

        self._symbols = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list(),
            "symbol",
        )

        # Will store the time.
        self._outputData.add(
            "time", "line", self.configuration["frames"]["time"], units="ps"
        )

        self._outputData.add(
            "mass_density", "line", (self._n_frames,), axis="time", units="g/cm3"
        )

        self._outputData.add(
            "atomic_density", "line", (self._n_frames,), axis="time", units="1/cm3"
        )

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        # get the Frame index
        frame_index = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frame_index)
        if not conf.is_periodic:
            raise DensityError(
                "Density cannot be computed for chemical system without periodc boundary conditions"
            )

        cell_volume = conf.unit_cell.volume * measure(1.0, "nm3").toval("cm3")

        atomic_density = self._n_atoms / cell_volume

        mass_density = (
            sum([ATOMS_DATABASE[s]["atomic_weight"] for s in self._symbols])
            / NAVOGADRO
            / cell_volume
        )

        return index, (atomic_density, mass_density)

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x:
        @type x: any.
        """

        self._outputData["atomic_density"][index] = x[0]

        self._outputData["mass_density"][index] = x[1]

    def finalize(self):
        """
        Finalize the job.
        """

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()


REGISTRY["den"] = Density
