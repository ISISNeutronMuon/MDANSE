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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import collections

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import generate_sphere_points
from MDANSE.Extensions import sas_fast_calc


class SolventAccessibleSurface(IJob):
    """
    The Solvent Accessible Surface (SAS) is the surface area of a molecule that is accessible to a solvent.
    SAS is typically calculated using the 'rolling ball' algorithm developed by Shrake & Rupley in 1973.

    * Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371.

    This algorithm uses a sphere (of solvent) of a particular radius to 'probe' the surface of the molecule.

    It involves constructing a mesh of points equidistant from each atom of the molecule
    and uses the number of these points that are solvent accessible to determine the surface area.
    The points are drawn at a water molecule's estimated radius beyond the van der Waals radius,
    which is effectively similar to 'rolling a ball' along the surface.
    All points are checked against the surface of neighboring atoms to determine whether they are buried or accessible.
    The number of points accessible is multiplied by the portion of surface area each point represents to calculate the SAS.
    The choice of the 'probe radius' has an effect on the observed surface area -
    using a smaller probe radius detects more surface details and therefore reports a larger surface.
    A typical value is 0.14 nm, which is approximately the radius of a water molecule.
    Another factor that affects the result is the definition of the VDW radii of the atoms in the molecule under study.
    """

    label = "Solvent Accessible Surface"

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, 2, 1)},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["n_sphere_points"] = ("IntegerConfigurator", {"mini": 1, "default": 1000})
    settings["probe_radius"] = ("FloatConfigurator", {"mini": 0.0, "default": 0.14})
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
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

        # Will store the solvent accessible surface.
        self._outputData.add(
            "sas",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="time",
            units="nm2",
        )

        # Generate the sphere points that will be used to evaluate the sas per atom.
        self.spherePoints = np.array(
            generate_sphere_points(self.configuration["n_sphere_points"]["value"]),
            dtype=np.float64,
        )
        # The solid angle increment used to convert the sas from a number of accessible point to a surface.
        self.solidAngleIncr = 4.0 * np.pi / len(self.spherePoints)

        # A mapping between the atom indexes and covalent_radius radius for the whole universe.
        self.vdwRadii = dict(
            [
                (
                    at.index,
                    ATOMS_DATABASE.get_atom_property(at.symbol, "covalent_radius"),
                )
                for at in self.configuration["trajectory"][
                    "instance"
                ].chemical_system.atom_list
            ]
        )
        self.vdwRadii_list = np.zeros(
            (max(self.vdwRadii.keys()) + 1, 2), dtype=np.float64
        )
        for k, v in self.vdwRadii.items():
            self.vdwRadii_list[k] = np.array([k, v])[:]

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

        # Fetch the configuration.
        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)

        # The configuration is made continuous.
        conf = conf.continuous_configuration()

        # Loop over the indexes of the selected atoms for the sas calculation.
        sas = sas_fast_calc.sas(
            conf["coordinates"],
            self._indexes,
            self.vdwRadii_list,
            self.spherePoints,
            self.configuration["probe_radius"]["value"],
        )

        return index, sas

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x: the output of run_step method.
        @type x: no specific type.
        """

        # The SAS is updated with the value obtained for frame |index|.
        self._outputData["sas"][index] = x

    def finalize(self):
        """
        Finalize the job.
        """

        # The SAS is converted from a number of accessible points to a surface.
        self._outputData["sas"] *= self.solidAngleIncr

        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
