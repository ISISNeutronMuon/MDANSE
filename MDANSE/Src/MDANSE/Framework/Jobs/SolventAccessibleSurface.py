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
    indices: list[int],
    grouping_map: list[int],
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
    occupations = dict.fromkeys(set(grouping_map), 0)
    for idx in indices:
        sphere_tree = KDTree(
            coords[idx] + sphere_points * (vdwRadii[idx] + probe_radius_value)
        )
        distance_dict = sphere_tree.sparse_distance_matrix(tree, max_distance=max_dist)
        pair_array = np.array(
            list(distance_dict.keys())
        )  # pairs of (sphere index, atom index)
        value_array = np.array(list(distance_dict.values()))
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
        blocked_for_sure = list(sphere_indices - free_for_sure)
        blocked_per_atom = collections.Counter(
            grouping_map[at_index]
            for at_index in combined_array[
                np.where(np.in1d(combined_array[:, 0], blocked_for_sure))
            ][:, 1].astype(int)
            if at_index < len(grouping_map)
        )
        scale_factor = (
            4 * np.pi * (vdwRadii[idx] + probe_radius_value) ** 2 / len(sphere_points)
        )
        sas += len(free_for_sure) * scale_factor
        for at_type, point_count in blocked_per_atom.items():
            occupations[at_type] += point_count * scale_factor
    return sas, occupations


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
                self._outputData.add(
                    f"sas/blocked_{mol_name}",
                    "LineOutputVariable",
                    (self.configuration["frames"]["number"],),
                    axis="sas/axes/time",
                    units="nm2",
                    main_result=True,
                )
                for mol_instance in self.trajectory.chemical_system._clusters[mol_name]:
                    all_indices -= set(mol_instance)
        for atom_name in {
            self.trajectory.chemical_system.atom_list[index] for index in all_indices
        }:
            self._outputData.add(
                f"sas/blocked_{atom_name}",
                "LineOutputVariable",
                (self.configuration["frames"]["number"],),
                axis="sas/axes/time",
                units="nm2",
                main_result=True,
            )
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
            temp_vdw_radii = [self.vdwRadii[atom_index] for atom_index in atom_indices]
        else:
            coords = conf["coordinates"]
            temp_vdw_radii = self.vdwRadii

        # Loop over the indices of the selected atoms for the sas calculation.
        sas_and_occupations = solvent_accessible_surface(
            coords,
            self.selected_indices,
            self.grouping_indices,
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
        sas, occupations = x
        # The SAS is updated with the value obtained for frame |index|.
        self._outputData["sas/total"][index] = sas
        self._outputData["sas/free"][index] = sas - sum(occupations.values())
        for atom_name, atom_index in self.type_mapping.items():
            surface = occupations.get(atom_index)
            self._outputData[f"sas/blocked_{atom_name}"][index] = (
                surface if surface else 0.0
            )
        for mol_name, mol_index in self.molecule_mapping.items():
            surface = occupations.get(mol_index)
            self._outputData[f"sas/blocked_{mol_name}"][index] = (
                surface if surface else 0.0
            )

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
