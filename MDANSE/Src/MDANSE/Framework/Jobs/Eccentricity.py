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

import numpy as np
from more_itertools import always_iterable

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import center_of_mass, moment_of_inertia


class Eccentricity(IJob):
    r"""Computes the eccentricity of a selected set of atoms.

    The eccentricity is calculated from the principal moments of
    inertia via the equation
    :math:`\sqrt{\text{pm3}^{2} - \text{pm1}^{2}} / \text{pm3}`
    where :math:`\text{pm1}` and :math:`\text{pm3}`
    are the smallest and largest principal moments of inertia
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
    settings["output_files"] = ("OutputFilesConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]

        self._outputData.add(
            "ecc/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )
        self._outputData.add(
            "ecc/eccentricity",
            "LineOutputVariable",
            np.zeros((self.configuration["frames"]["number"]), dtype=np.float64),
            axis="ecc/axes/time",
            main_result=True,
        )

        self._atoms = self.trajectory.atom_names
        self._indices = self.trajectory.atom_indices
        self._selectionMasses = np.array(
            [
                self.trajectory.get_atom_property(element, "atomic_weight")
                for element in always_iterable(
                    self.trajectory.selection_getter(self._atoms)
                )
            ]
        )

    def run_step(self, index: int):
        """Calculate the eccentricity for the selected atoms at the
        frame index.

        Parameters
        ----------
        index : int
            The frame index.
        """
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.trajectory.configuration(frameIndex)
        conf = conf.contiguous_configuration()
        series = conf["coordinates"][self._indices, :]

        com = center_of_mass(series, masses=self._selectionMasses)

        # calculate the inertia moments
        mass = np.array(self._selectionMasses)

        moi = moment_of_inertia(series, com, mass)
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
        self._outputData["ecc/eccentricity"][frame_idx] = eccentricity

    def finalize(self):
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
