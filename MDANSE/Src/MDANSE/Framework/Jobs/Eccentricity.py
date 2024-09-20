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
from MDANSE.Mathematics.Geometry import center_of_mass
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class Eccentricity(IJob):
    """Computes the eccentricity for a set of atoms e.g. in a micelle.
    The eccentricity is calculated from the principal moments of
    inertia via the equation sqrt(pm3**2 - pm1**2) / pm3 where pm1 and
    pm3 are the smallest and largest principal moments of inertia
    respectively. Therefore, for a spherically symmetric molecule its
    eccentricity will be 0 while for an aspherical molecule like CO2 its
    eccentricity will be 1. This job follows the equations used in rdkit
    which was itself taken from https://doi.org/10.1002/9783527618279.ch37.
    """
    label = "Eccentricity"

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
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )
        self._outputData.add(
            "eccentricity",
            "LineOutputVariable",
            np.zeros((self.configuration["frames"]["number"]), dtype=np.float64),
            axis="time",
            main_result=True,
        )

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )
        self._indexes = np.array([
            idx
            for idxs in self._configuration["atom_selection"]["indexes"]
            for idx in idxs
        ])
        self._selectionMasses = np.array([
            m
            for masses in self._configuration["atom_selection"]["masses"]
            for m in masses
        ])

    def run_step(self, index: int):
        """Calculate the eccentricity for the selected atoms at the
        frame index.

        Parameters
        ----------
        index : int
            The frame index.
        """
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)
        conf = conf.continuous_configuration()
        series = conf["coordinates"][self._indexes, :]

        com = center_of_mass(series, masses=self._selectionMasses)

        # calculate the inertia moments
        mass = np.array(self._selectionMasses)
        x, y, z = (series - com).T
        xx = np.sum(mass * (y**2 + z**2))
        xy = np.sum(-mass * x * y)
        xz = np.sum(-mass * x * z)
        yy = np.sum(mass * (x**2 + z**2))
        yz = np.sum(-mass * y * z)
        zz = np.sum(mass * (x**2 + y**2))

        moi = np.array(
            [
                [xx, xy, xz],
                [xy, yy, yz],
                [xz, yz, zz],
            ]
        )

        pm1, pm2, pm3 = np.linalg.eigvalsh(moi)
        eccentricity = np.sqrt(pm3**2 - pm1**2) / pm3
        return index, eccentricity

    def combine(self, frame_idx: int, eccentricity: float):
        """Save the calculated eccentricity of the selected atoms.

        Parameters
        ----------
        frame_idx : int
            The frame index.
        eccentricity : float
            The eccentricity for the selected atom at frame_idx.
        """
        self._outputData["eccentricity"][frame_idx] = eccentricity

    def finalize(self):
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
