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
from scipy.spatial import KDTree

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import generate_sphere_points
from MDANSE.MolecularDynamics.Configuration import padded_coordinates


def solvent_accessible_surface(
    coords: np.ndarray,
    indexes: list[int],
    vdwRadii: np.ndarray,
    sphere_points: np.ndarray,
    probe_radius_value: float,
):
    # Computes the Solvent Accessible Surface Based on the algorithm published by Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371.

    sas = 0.0
    tree = KDTree(coords)
    max_dist = np.max(vdwRadii) + probe_radius_value
    min_dist = np.min(vdwRadii) + probe_radius_value
    sphere_indices = set(range(len(sphere_points)))
    for idx in indexes:
        sphere_tree = KDTree(
            coords[idx] + sphere_points * (vdwRadii[idx] + probe_radius_value)
        )
        distance_dict = sphere_tree.sparse_distance_matrix(tree, max_distance=max_dist)
        pair_array = np.array([pair for pair in distance_dict.keys()])
        value_array = np.array([value for value in distance_dict.values()])
        combined_array = np.hstack(
            [pair_array, value_array.reshape((len(value_array), 1))]
        )[np.where(pair_array[:, 1] != idx)]
        blocked_for_sure = set(
            combined_array[:, 0][np.where(combined_array[:, 2] <= min_dist)]
        )
        free_for_sure = sphere_indices - set(combined_array[:, 0])
        uncertain = sphere_indices - free_for_sure - blocked_for_sure
        confirmed = set()
        if len(uncertain) > 0:
            uncertain_lines = np.array(
                [line for line in combined_array if line[0] in uncertain]
            )
            neighbour_radii = np.array(
                [vdwRadii[int(line[1])] for line in uncertain_lines]
            )
            confirmed = set(
                uncertain_lines[:, 0][
                    np.where(
                        uncertain_lines[:, 2] < neighbour_radii + probe_radius_value
                    )
                ]
            )
        free_for_sure.update(uncertain - confirmed)
        sas += (
            len(free_for_sure)
            / len(sphere_points)
            * 4
            * np.pi
            * (vdwRadii[idx] + probe_radius_value) ** 2
        )
    return sas


class SolventAccessibleSurface(IJob):
    """Calculates the accessible surface of the selected atoms.

    Please keep in mind that the atoms outside of the selection are still considered to
    be blocking the accessible surface. If you are interested in the **total** surface
    of a group of atoms, please remove the other atoms from the trajectory.

    Solvent Accessible Surface is calculated using the 'rolling ball' algorithm
    developed by Shrake & Rupley in 1973.

    * Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371.

    This algorithm uses a sphere (of solvent) of a particular radius to 'probe' the
    surface of the molecule.

    It involves constructing a mesh of points equidistant from each atom of the molecule
    and uses the number of these points that are solvent accessible to determine the
    surface area. The points are drawn at a water molecule's estimated radius beyond
    the van der Waals radius, which is effectively similar to 'rolling a ball' along
    the surface. All points are checked against the surface of neighboring atoms
    to determine whether they are buried or accessible. The number of points
    accessible is multiplied by the portion of surface area each point represents
    to calculate the SAS.

    The choice of the 'probe radius' has an effect on the observed surface area -
    using a smaller probe radius detects more surface details and therefore reports
    a larger surface. A typical value is 0.14 nm, which is approximately the radius
    of a water molecule. Another factor that affects the result is the definition
    of the VDW radii of the atoms in the molecule under study.
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
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]

        # Will store the time.
        self._outputData.add(
            "sas/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        # Will store the solvent accessible surface.
        self._outputData.add(
            "sas/sas",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="sas/axes/time",
            units="nm2",
            main_result=True,
        )

        # Generate the sphere points that will be used to evaluate the sas per atom.
        self.spherePoints = np.array(
            generate_sphere_points(self.configuration["n_sphere_points"]["value"]),
            dtype=np.float64,
        )

        # A mapping between the atom indices and covalent_radius radius for the whole universe.
        self.vdwRadii = self.configuration["trajectory"][
            "instance"
        ].chemical_system.atom_property("vdw_radius")  # should it be covalent?

        self._indices = self.trajectory.atom_indices

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        # This is the actual index of the frame corresponding to the loop index.
        frameIndex = self.configuration["frames"]["value"][index]

        # Fetch the configuration.
        conf = self.trajectory.configuration(frameIndex)

        # The configuration is made continuous.
        conf = conf.continuous_configuration()
        unit_cell = conf._unit_cell

        if conf.is_periodic:
            padding_thickness = 1.05 * max(
                self.configuration["probe_radius"]["value"], np.max(self.vdwRadii)
            )
            coords, atom_indices = padded_coordinates(
                conf["coordinates"],
                unit_cell,
                padding_thickness,
            )
            temp_vdw_radii = [self.vdwRadii[atom_index] for atom_index in atom_indices]
        else:
            coords = conf["coordinates"]
            temp_vdw_radii = self.vdwRadii

        # Loop over the indices of the selected atoms for the sas calculation.
        sas = solvent_accessible_surface(
            coords,
            self._indices,
            temp_vdw_radii,
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
        self._outputData["sas/sas"][index] = x

    def finalize(self):
        """
        Finalize the job.
        """

        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
