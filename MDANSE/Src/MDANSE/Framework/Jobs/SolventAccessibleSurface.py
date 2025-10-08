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
import numpy.typing as npt
from scipy.spatial import KDTree

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import generate_sphere_points
from MDANSE.MolecularDynamics.Configuration import padded_coordinates


def compare_trees(
    sphere_tree: KDTree,
    atom_tree: KDTree,
    sphere_indices: set[int],
    vdw_radii: npt.NDArray[float],
    max_dist: float,
    min_dist: float,
    atom_index: int | None,
    probe_radius: float,
) -> tuple[set[int], list[int]]:
    """Count how many points from sphere_tree are blocked by atom_tree.

    The assumption is that each point in atom_tree is blocking a volume within
    a van der Waals radius around itself.

    Parameters
    ----------
    sphere_tree : KDTree
        Sampling points on a sphere around a reference point (atom) in a KDTree.
    atom_tree : KDTree
        Atom positions in a KDTree.
    sphere_indices : set[int]
        Set of indices of all the points on the sphere.
    vdw_radii : npt.NDArray[float]
        Array of van der Waals radii for all the point in atom_tree.
    max_dist : float
        Distance between points above which blocking is not possible.
    min_dist : float
        Distanbe between point below which blocking is certain.
    atom_index : int | None
        Index of the reference atom (i.e. centre of sphere_tree) in atom_tree.
    probe_radius : float
        Radius of the assumed probe particle that should fit on the surface.

    Returns
    -------
    tuple[set[int], set[int]]
        Indices of free sphere points, indices of blocked sphere points.
    """
    distance_dict = sphere_tree.sparse_distance_matrix(atom_tree, max_distance=max_dist)
    pair_array = np.array(
        list(distance_dict.keys())
    )  # pairs of (sphere index, atom index)
    value_array = np.array(list(distance_dict.values()))
    combined_array = (
        np.hstack([pair_array, value_array.reshape((len(value_array), 1))])[
            np.where(pair_array[:, 1] != atom_index)
        ]
        if atom_index is not None
        else np.hstack([pair_array, value_array.reshape((len(value_array), 1))])
    )
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
            [vdw_radii[int(line[1])] for line in uncertain_lines]
        )
        confirmed = set(
            uncertain_lines[:, 0][
                np.where(uncertain_lines[:, 2] < neighbour_radii + probe_radius)
            ]
        )
    free_for_sure.update(uncertain - confirmed)
    blocked_for_sure = sphere_indices - free_for_sure
    return free_for_sure, blocked_for_sure


def solvent_accessible_surface(
    coords: npt.NDArray[float],
    all_indices: npt.NDArray[int],
    selected_indices: list[int],
    vdw_radii: npt.NDArray[float],
    sphere_points: npt.NDArray[float],
    probe_radius_value: float,
):
    """Calculate the total surface are of a group of atoms, and how much is blocked.

    Coordinates of all atoms are used in this analysis. The selected atoms are the
    ones for which the surface area is calculated. The atoms that are not in the
    selection are still considered in the analysis, since they can block the
    accessible surface.

    Parameters
    ----------
    coords : np.ndarray
        Coordinates of all atoms plus their copies in padding region.
    indices : list[int]
        Indices of atoms belonging to the selection.
    vdwRadii : np.ndarray
        For each atom, its van der Waals radius.
    sphere_points : np.ndarray
        Coordinates of points on a sphere.
    probe_radius_value : float
        Radius of the probe particle.

    Returns
    -------
    float, npt.NDArray[float]
        Total surface, blocked surface per atom
    """
    # Computes the Solvent Accessible Surface Based on the algorithm published by Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371.
    total_sas = 0.0
    current_sas = 0.0
    atom_tree = KDTree(coords)
    max_dist = np.max(vdw_radii) + probe_radius_value
    min_dist = np.min(vdw_radii) + probe_radius_value
    sphere_indices = set(range(len(sphere_points)))
    for idx in selected_indices:
        sphere_tree = KDTree(
            coords[idx] + sphere_points * (vdw_radii[idx] + probe_radius_value)
        )
        inner_selection = np.where(
            np.isin(all_indices, list(set(selected_indices) - {idx}))
        )
        inner_tree = KDTree(coords[inner_selection])
        inner_vdw = vdw_radii[inner_selection]
        total_free, _ = compare_trees(
            sphere_tree,
            inner_tree,
            sphere_indices,
            inner_vdw,
            max_dist,
            min_dist,
            None,
            probe_radius_value,
        )
        free_for_sure, _ = compare_trees(
            sphere_tree,
            atom_tree,
            sphere_indices,
            vdw_radii,
            max_dist,
            min_dist,
            idx,
            probe_radius_value,
        )
        scale_factor = (
            4 * np.pi * (vdw_radii[idx] + probe_radius_value) ** 2 / len(sphere_points)
        )
        total_sas += len(total_free) * scale_factor
        current_sas += len(free_for_sure) * scale_factor
    return total_sas, current_sas


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
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
            }
        },
    )
    settings["n_sphere_points"] = ("IntegerConfigurator", {"mini": 1, "default": 1000})
    settings["probe_radius"] = ("FloatConfigurator", {"mini": 0.0, "default": 0.14})
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]
        self.type_mapping = {}
        self.molecule_mapping = {}

        # Will store the time.
        self._outputData.add(
            "sas/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        # Will store the solvent accessible surface.
        self._outputData.add(
            "sas/total",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="sas/axes/time",
            units="nm2",
            main_result=True,
        )
        self._outputData.add(
            "sas/free",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="sas/axes/time",
            units="nm2",
            main_result=True,
        )
        all_indices = self.trajectory.chemical_system.all_indices
        self.grouping_indices = len(all_indices) * [0]
        loose_atoms = []
        if self.configuration["grouping_level"]["value"] == "molecule":
            for mol_name in self.trajectory.chemical_system.unique_molecules():
                for mol_instance in self.trajectory.chemical_system._clusters[mol_name]:
                    all_indices -= set(mol_instance)
        for atom_name in {
            self.trajectory.chemical_system.atom_list[index] for index in all_indices
        }:
            loose_atoms.append(atom_name)

        # Generate the sphere points that will be used to evaluate the sas per atom.
        self.spherePoints = np.array(
            generate_sphere_points(self.configuration["n_sphere_points"]["value"]),
            dtype=np.float64,
        )

        # A mapping between the atom indices and covalent_radius radius for the whole universe.
        self.vdwRadii = self.configuration["trajectory"][
            "instance"
        ].chemical_system.atom_property("vdw_radius")

        self.selected_indices = self.trajectory.atom_indices
        self.all_indices = self.trajectory.chemical_system.all_indices
        atom_types = self.trajectory.chemical_system.atom_list
        self.type_mapping = {
            atom_type: index + 1 for index, atom_type in enumerate(loose_atoms)
        }
        for index in all_indices:
            self.grouping_indices[index] = self.type_mapping[atom_types[index]]

        if self.configuration["grouping_level"]["value"] == "molecule":
            self.molecule_mapping = {
                mol_name: -index - 1
                for index, mol_name in enumerate(
                    self.trajectory.chemical_system.unique_molecules()
                )
            }
            for mol_name in self.trajectory.chemical_system.unique_molecules():
                for index in self.trajectory.chemical_system._clusters[mol_name]:
                    self.grouping_indices[index] = self.molecule_mapping[mol_name]

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
            temp_vdw_radii = np.array(
                [self.vdwRadii[atom_index] for atom_index in atom_indices]
            )
        else:
            coords = conf["coordinates"]
            temp_vdw_radii = self.vdwRadii

        # Loop over the indices of the selected atoms for the sas calculation.
        sas_and_occupations = solvent_accessible_surface(
            coords,
            atom_indices,
            self.selected_indices,
            temp_vdw_radii,
            self.spherePoints,
            self.configuration["probe_radius"]["value"],
        )

        return index, sas_and_occupations

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x: the output of run_step method.
        @type x: no specific type.
        """
        total_sas, current_sas = x
        # The SAS is updated with the value obtained for frame |index|.
        self._outputData["sas/total"][index] = total_sas
        self._outputData["sas/free"][index] = current_sas

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
