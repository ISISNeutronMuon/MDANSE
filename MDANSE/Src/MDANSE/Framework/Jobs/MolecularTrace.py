# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/MolecularTrace.py
# @brief     Implements module/class/test MolecularTrace
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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Extensions import mt_fast_calc


class MolecularTrace(IJob):
    """
    A Molecular Trace is a time-integrated trace of selected atoms in terms of their coordinates.

    * the minimal and maximal coordinates from the selected atomic trajectories are computed.
    * based on these min/max and a spatial resolution, a cartesian grid is constructed.
    * for each atom and for each frame of the selected trajectories, a histogram of presence, called the spatial density, is constructed.

    The molecular trace can reveal anisotropic vibrations and diffusion pathways.

    **Acknowledgement and publication:**\n
    Gael Goret, PELLEGRINI Eric

    """

    label = "Molecular Trace"

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["spatial_resolution"] = (
        "FloatConfigurator",
        {"mini": 0.01, "default": 0.1},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "ASCIIFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        self.numberOfSteps = self.configuration["frames"]["number"]

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        # Generate the grids that will be used to quantify the presence of atoms in an area.
        self.resolution = self.configuration["spatial_resolution"]["value"]

        maxx, maxy, maxz = 0, 0, 0
        minx, miny, minz = 10**9, 10**9, 10**9
        for i in range(self.numberOfSteps):
            frameIndex = self.configuration["frames"]["value"][i]
            conf = self.configuration["trajectory"]["instance"].configuration(
                frameIndex
            )
            conf = conf.continuous_configuration()
            coords = conf["coordinates"]

            minx_loc = coords[:, 0].min()
            miny_loc = coords[:, 1].min()
            minz_loc = coords[:, 2].min()

            maxx_loc = coords[:, 0].max()
            maxy_loc = coords[:, 1].max()
            maxz_loc = coords[:, 2].max()

            maxx = max(maxx_loc, maxx)
            maxy = max(maxy_loc, maxy)
            maxz = max(maxz_loc, maxz)

            minx = min(minx, minx_loc)
            miny = min(miny, miny_loc)
            minz = min(minz, minz_loc)

        dimx = maxx - minx
        dimy = maxy - miny
        dimz = maxz - minz

        self.min = np.array([minx, miny, minz], dtype=np.float64)
        self._outputData.add("origin", "LineOutputVariable", self.min, units="nm")

        self.gdim = np.ceil(np.array([dimx, dimy, dimz]) / self.resolution).astype(int)
        spacing = self.configuration["spatial_resolution"]["value"]
        self._outputData.add(
            "spacing",
            "LineOutputVariable",
            np.array([spacing, spacing, spacing]),
            units="nm",
        )
        self.grid = np.zeros(self.gdim, dtype=np.int32)

        self._outputData.add(
            "molecular_trace",
            "VolumeOutputVariable",
            tuple(np.ceil(np.array([dimx, dimy, dimz]) / self.resolution).astype(int)),
        )

        self._indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        # This is the actual index of the frame corresponding to the loop index.
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)
        conf = conf.continuous_configuration()

        grid = np.zeros(self.gdim, dtype=np.int32)

        # Loop over the indexes of the selected atoms for the molecular trace calculation.
        mt_fast_calc.mt(
            conf["coordinates"][self._indexes, :],
            grid,
            self.configuration["spatial_resolution"]["value"],
            self.min,
        )

        return index, grid

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x: the output of run_step method.
        @type x: no specific type.
        """

        np.add(self.grid, x, self.grid)

    def finalize(self):
        """
        Finalize the job.
        """

        self._outputData["molecular_trace"][:] = self.grid

        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
