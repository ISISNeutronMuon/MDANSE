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
import copy
from collections.abc import Sequence

import numpy as np
import numpy.typing as npt
from scipy.spatial import KDTree

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Geometry import generate_sphere_points
from MDANSE.MolecularDynamics.Configuration import padded_coordinates
from MDANSE.MolecularDynamics.Trajectory import Trajectory


def compare_trees(
    sphere_tree: KDTree,
    atom_tree: KDTree,
    sphere_indices: set[int],
    vdw_radii: npt.NDArray[float],
    max_dist: float,
    min_dist: float,
    probe_radius: float,
) -> set[int]:
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
    probe_radius : float
        Radius of the assumed probe particle that should fit on the surface.

    Returns
    -------
    set[int]
        Indices of free sphere points, indices of blocked sphere points.
    """
    distance_dict = sphere_tree.sparse_distance_matrix(
        atom_tree, max_distance=1.5 * max_dist
    )
    pair_array = np.array(
        list(distance_dict.keys())
    )  # pairs of (sphere index, atom index)
    value_array = np.array(list(distance_dict.values()))
    if not len(value_array):
        return sphere_indices
    combined_array = np.hstack([pair_array, value_array.reshape((len(value_array), 1))])
    blocked_for_sure = set(
        combined_array[:, 0][np.where(combined_array[:, 2] <= min_dist)]
    )
    free_for_sure = sphere_indices - set(combined_array[:, 0])
    uncertain = sphere_indices - free_for_sure - blocked_for_sure
    confirmed = set()
    if uncertain:
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
    return free_for_sure


def solvent_accessible_surface(
    coords: npt.NDArray[float],
    all_indices: npt.NDArray[int],
    selected_indices: Sequence[int],
    grouping_indices: npt.NDArray[int],
    vdw_radii: npt.NDArray[float],
    sphere_points: npt.NDArray[float],
    probe_radius_value: float,
    *,
    calculate_blocking: bool = False,
) -> tuple[float, float, dict[int, float]]:
    """Calculate the total accessible surface of the selected atoms.

    Coordinates of all atoms are used in this analysis.
    The total surface is calculated considering only the selected atoms,
    based on how many sphere points around each selected atom are within
    a radius from other selected atoms, and therefore blocked.
    Free surface is calculated as a number of sphere points around the
    selected atoms that are not blocked by ANY atoms, selected or not.
    Blocked surface (calculated if calculate_blocking=True) checks which
    points on the sphere are within the cutoff radius from specific atoms
    outside the selection. The blocked surfaces are not additive, as it is
    possible for a point to be blocked by more that one atom at the same time.

    Parameters
    ----------
    coords : np.ndarray[float]
        Coordinates of all atoms plus their copies in padding region.
    all_indices : np.ndarray[int]
        An array of all the atom indices.
    indices : Sequence[int]
        Indices of only the selected atoms.
    grouping_indices : np.ndarray[int]
        Index of the results group (e.g. 'Cu', '<H2_O1>/H') to which each atom belongs.
    vdw_radii : np.ndarray
        For each atom, its van der Waals radius.
    sphere_points : np.ndarray
        Pre-generated near-equidistant points on a sphere.
    probe_radius_value : float
        Radius of the probe particle.
    calculate_blocking : bool, default False
        If True, the fraction of the surface blocked by different atoms will be calculated.

    Returns
    -------
    float, float, dict[int, float]
        Total surface, free surface, blocked surface per atom
    """
    # Computes the Solvent Accessible Surface Based on the algorithm published by Shrake, A., and J. A. Rupley. JMB (1973) 79:351-371.
    total_sas = 0.0
    free_sas = 0.0
    max_dist = np.max(vdw_radii) + probe_radius_value
    min_dist = np.min(vdw_radii) + probe_radius_value
    sphere_indices = set(range(len(sphere_points)))
    selected_set = set(selected_indices)
    blockers = set(grouping_indices) - {0}
    blocking_indices = {
        blocker: set(np.where(grouping_indices == blocker)[0]) - selected_set
        for blocker in blockers
    }
    blocked_sas = dict.fromkeys(blockers, 0.0)
    for idx in selected_indices:
        sphere_coords = coords[idx] + sphere_points * (
            vdw_radii[idx] + probe_radius_value
        )
        sphere_tree = KDTree(sphere_coords)
        inner_selection = np.where(np.isin(all_indices, list(selected_set - {idx})))
        inner_tree = KDTree(coords[inner_selection])
        inner_vdw = vdw_radii[inner_selection]
        total_free = compare_trees(
            sphere_tree,
            inner_tree,
            sphere_indices,
            inner_vdw,
            max_dist,
            min_dist,
            probe_radius_value,
        )
        scale_factor = (
            4 * np.pi * (vdw_radii[idx] + probe_radius_value) ** 2 / len(sphere_points)
        )
        total_sas += len(total_free) * scale_factor
        if calculate_blocking:
            final_free = copy.copy(total_free)
            free_sphere_tree = KDTree(sphere_coords[list(total_free)])
            sphere_mapping = dict(enumerate(total_free))
            for blocker, indices in blocking_indices.items():
                blocking_selection = np.where(
                    np.isin(all_indices, list(indices - {idx} - selected_set))
                )
                if len(blocking_selection[0]):
                    blocking_tree = KDTree(coords[blocking_selection])
                    remaining_free = compare_trees(
                        free_sphere_tree,
                        blocking_tree,
                        set(range(len(total_free))),
                        vdw_radii[blocking_selection],
                        max_dist,
                        min_dist,
                        probe_radius_value,
                    )
                    blocked_points = total_free - {
                        sphere_mapping[simple_index] for simple_index in remaining_free
                    }
                    blocked_sas[blocker] += (len(blocked_points)) * scale_factor
                    final_free -= blocked_points
            free_sas += len(final_free) * scale_factor
    return total_sas, free_sas, blocked_sas


def create_type_mapping(
    atom_types: Sequence[str],
    grouping_level: str,
    molecule_names: Sequence[str] | None = None,
    atoms_in_molecule: dict[str, Sequence[str]] | None = None,
) -> tuple[dict[str, int], dict[int, str]]:
    """Create the arbitrary indices used for grouping in the SAS analysis.

    This function returns two dictionaries, one mapping atom type strings
    to numbers, and other mapping numbers to string keys that are also
    used in the analysis output data.

    Parameters
    ----------
    atom_types : Sequence[str]
        List of all atom types given as str, one entry per atom.
    grouping_level : str
        Either "atom" or "molecule".
    molecule_names : Sequence[str] | None, optional
        Unique molecule names, not needed for "atom" grouping, by default None
    atoms_in_molecule : dict[str, Sequence[str]] | None, optional
        Atom types in each molecule type, not needed for "atom" grouping, by default None

    Returns
    -------
    tuple[dict[str, int], dict[int, str]]
        Two dicts: {atom_type: unique_number} pairs and {unique_number: output_data_key} pairs.
    """
    type_mapping = {
        atom_type: index + 1 for index, atom_type in enumerate(set(atom_types))
    }
    grouping_keys = {
        arb_index: atom_type for atom_type, arb_index in type_mapping.items()
    }

    next_index = max(type_mapping.values()) + 1 if type_mapping else 1
    if grouping_level == "molecule":
        for mol_name in molecule_names:
            for atom_name in atoms_in_molecule[mol_name]:
                new_key = f"<{mol_name}>/{atom_name}"
                type_mapping[new_key] = next_index
                grouping_keys[next_index] = new_key
                next_index += 1
    return type_mapping, grouping_keys


def make_grouping_indices(
    all_indices: Sequence[int],
    selected_indices: Sequence[int],
    atom_types: Sequence[str],
    type_mapping: dict[str, int],
    grouping_level: str,
    cs_clusters: dict[str, list[int]],
) -> npt.NDArray[int]:
    """Assign each atom the number of its corresponding dataset in the output data.

    Parameters
    ----------
    all_indices : Sequence[int]
        List of all atom indices.
    selected_indices : Sequence[int]
        List of indices in the atom selection
    atom_types : Sequence[str]
        List of chemical element symbols for each atom
    type_mapping : dict[str, int]
        The dictionary of unique indices for every atom type.
    grouping_level : str
        Either "atom" or "molecule"
    cs_clusters : dict[str, list[int]]
        The _clusters object from Trajectory.chemical_system.

    Returns
    -------
    npt.NDArray[int]
        For each atom, a number representing its group in the output data.
    """
    grouping_indices = len(all_indices) * [0]
    grouping_indices = [type_mapping[atom] for atom in atom_types]
    if grouping_level == "molecule":
        reference_set = set(all_indices) - set(selected_indices)
        for mol_name, mol_clusters in cs_clusters.items():
            for mol_instance in mol_clusters:
                if reference_set.issuperset(mol_instance):
                    for at_index in mol_instance:
                        grouping_indices[at_index] = type_mapping[
                            f"<{mol_name}>/{atom_types[at_index]}"
                        ]
    grouping_indices = np.array(grouping_indices)
    grouping_indices[selected_indices] = 0
    return grouping_indices


def identify_loose_atoms(
    trajectory: Trajectory, grouping_level: str
) -> tuple[dict[str, list[str]], Sequence[str]]:
    """Find all the atoms that need to be included in the output outside of molecules.

    Parameters
    ----------
    trajectory : Trajectory
        The current trajectory with all the selection/transmutation applied.
    grouping_level : str
        Either "atom" or "molecule"

    Returns
    -------
    tuple[dict[str, list[str]], Sequence[str]]
        Dictionary of atom types in each molecule type, list of atom types outside molecules
    """
    all_indices = copy.deepcopy(trajectory.chemical_system.all_indices)
    atom_types = np.array(trajectory.chemical_system.atom_list)
    atoms_in_molecule = {}
    if grouping_level == "molecule":
        for mol_name in trajectory.chemical_system.unique_molecules():
            atoms_in_molecule.setdefault(mol_name, set())
            for mol_instance in trajectory.chemical_system._clusters[mol_name]:
                all_indices -= set(mol_instance)
                atoms_in_molecule[mol_name].update(atom_types[mol_instance])
    loose_atoms = list(
        {trajectory.chemical_system.atom_list[index] for index in all_indices}
    )
    return atoms_in_molecule, loose_atoms


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
    PREDICTORS = ("frames",)

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
    settings["radius_type"] = (
        "SingleChoiceConfigurator",
        {
            "label": "Use van der Waals radius (adsorption) or covalent radius (chemisorption)",
            "choices": ["van der Waals", "covalent"],
            "default": "van der Waals",
        },
    )
    settings["calculate_blocked_surface"] = (
        "BooleanConfigurator",
        {
            "default": False,
            "label": "Run additional calculations to check which atoms outside the selection are blocking the surface of the selected atoms.",
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.check_blocking = self.configuration["calculate_blocked_surface"]["value"]
        self.numberOfSteps = self.configuration["frames"]["number"]
        self.type_mapping = {}
        self.molecule_mapping = {}
        self.grouping_keys = {}

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

        atoms_in_molecule, loose_atoms = identify_loose_atoms(
            self.trajectory, self.configuration["grouping_level"]["value"]
        )

        # Generate the sphere points that will be used to evaluate the sas per atom.
        self.spherePoints = np.array(
            generate_sphere_points(self.configuration["n_sphere_points"]["value"]),
            dtype=np.float64,
        )

        # A mapping between the atom indices and covalent_radius radius for the whole universe.
        if self.configuration["radius_type"]["value"] == "van der Waals":
            self.vdwRadii = self.configuration["trajectory"][
                "instance"
            ].chemical_system.atom_property("vdw_radius")
        elif self.configuration["radius_type"]["value"] == "covalent":
            self.vdwRadii = self.configuration["trajectory"][
                "instance"
            ].chemical_system.atom_property("covalent_radius")
        else:
            raise NotImplementedError(
                f"Property {self.configuration['radius_type']['value']} cannot be used as radius in the SAS calculation."
            )

        self.selected_indices = self.trajectory.atom_indices
        atom_types = self.trajectory.chemical_system.atom_list

        self.type_mapping, self.grouping_keys = create_type_mapping(
            atom_types,
            self.configuration["grouping_level"]["value"],
            molecule_names=set(self.trajectory.chemical_system._clusters),
            atoms_in_molecule=atoms_in_molecule,
        )

        if self.check_blocking:
            self._outputData.add(
                "sas/free",
                "LineOutputVariable",
                (self.configuration["frames"]["number"],),
                axis="sas/axes/time",
                units="nm2",
                main_result=True,
            )
            for result_key in self.type_mapping:
                if "/" in result_key or result_key in loose_atoms:
                    self._outputData.add(
                        f"sas/taken/{result_key}",
                        "LineOutputVariable",
                        (self.configuration["frames"]["number"],),
                        axis="sas/axes/time",
                        units="nm2",
                        main_result=False,
                    )
        self.grouping_indices = make_grouping_indices(
            self.trajectory.chemical_system.all_indices,
            self.selected_indices,
            atom_types,
            self.type_mapping,
            self.configuration["grouping_level"]["value"],
            self.trajectory.chemical_system._clusters,
        )

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
            padding_thickness = 1.05 * (
                self.configuration["probe_radius"]["value"] + np.max(self.vdwRadii)
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
            self.grouping_indices,
            temp_vdw_radii,
            self.spherePoints,
            self.configuration["probe_radius"]["value"],
            calculate_blocking=self.check_blocking,
        )

        return index, sas_and_occupations

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x: the output of run_step method.
        @type x: no specific type.
        """
        total_sas, free_sas, blocked_sas = x
        # The SAS is updated with the value obtained for frame |index|.
        self._outputData["sas/total"][index] = total_sas
        if self.check_blocking:
            for type_index, surface in blocked_sas.items():
                self._outputData[f"sas/taken/{self.grouping_keys[type_index]}"][
                    index
                ] = surface
            self._outputData["sas/free"][index] = free_sas

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
