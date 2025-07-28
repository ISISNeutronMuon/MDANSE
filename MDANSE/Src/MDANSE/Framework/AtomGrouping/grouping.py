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

import itertools as it
from collections.abc import Iterable
from typing import Callable

import numpy.typing as npt

from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
from MDANSE.Mathematics.Arithmetic import weighted_sum
from MDANSE.MolecularDynamics.Trajectory import Trajectory

GROUP_TEMPLATE = "{}/<{}>/{}"
PAIR_GROUP_TEMPLATE = "{}/<{}><{}>/{}"


def add_grouped_totals(
    trajectory: Trajectory,
    output_data: OutputData,
    result_name: str,
    data_type: str,
    dim: int = 1,
    conc_exp: float = 1.0,
    *,
    intra: bool = False,
    scaling_factor: bool = True,
    post_func: Callable[[npt.NDArray], npt.NDArray] = lambda x: x,
    post_label: str = "total",
    **kwargs,
):
    """Add the grouped totals to the output data.

    Parameters
    ----------
    trajectory: Trajectory
        Current state of the trajectory, including selection and transmutation
    output_data : dict[str, npt.NDArray]
        Dictionary of data arrays containing analysis results.
    result_name : str
        The name of the results.
    data_type : str
        The plotting type of the data.
    dim : int
        Number of repeats of the elements.
    conc_exp : float
        The exponent the at the product of the concentrations are taken
        to (e.g. (c_i * c_j)**0.5 which is used for DCSF jobs).
    intra: bool
        Add total results for intra results.
    scaling_factor: bool
        Add the scaling factor to the output data if True.
    post_func: Callable[[npt.NDArray], npt.NDArray]
        A function which is applied to the results.
    post_label: str
        The label to be added for grouped summed results.
    """
    if trajectory._grouping_level == "atom":
        return

    if dim == 1:
        add_grouped_totals_1D(
            trajectory,
            output_data,
            result_name,
            data_type,
            scaling_factor=scaling_factor,
            post_func=post_func,
            post_label=post_label,
            **kwargs,
        )
    elif dim == 2:
        add_grouped_totals_2D(
            trajectory,
            output_data,
            result_name,
            data_type,
            conc_exp,
            intra=intra,
            scaling_factor=scaling_factor,
            post_func=post_func,
            post_label=post_label,
            **kwargs,
        )
    else:
        raise NotImplementedError("Grouped total for dim > 2 not implemented.")


def add_grouped_totals_1D(
    trajectory: Trajectory,
    output_data: OutputData,
    result_name: str,
    data_type: str,
    *,
    scaling_factor: bool = True,
    post_func: Callable[[npt.NDArray], npt.NDArray] = lambda x: x,
    post_label: str = "total",
    **kwargs,
):
    """Add the grouped totals to the output data.

    Parameters
    ----------
    trajectory: Trajectory
        Current state of the trajectory, including selection and transmutation
    output_data : dict[str, npt.NDArray]
        Dictionary of data arrays containing analysis results.
    result_name : str
        The name of the results.
    data_type : str
        The plotting type of the data.
    scaling_factor: bool
        Add the scaling factor to the output data if True.
    post_func: Callable[[npt.NDArray], npt.NDArray]
        A function which is applied to the results.
    post_label: str
        The label to be added for grouped summed results.
    """
    tot_n_atms = len(trajectory.atom_indices)

    for grp in trajectory.group_lookup:
        grp_ele = sorted(
            {
                trajectory.atom_types[x]
                for cluster in trajectory.chemical_system._clusters[grp]
                for x in cluster
                if x in trajectory.atom_indices
            }
        )
        conc = trajectory.group_lookup[grp] / tot_n_atms
        labels = [((grp, ele), "") for ele in grp_ele]
        group_id = GROUP_TEMPLATE.format(result_name, grp, post_label)

        results = weighted_sum(output_data, result_name + "/<%s>/%s", labels) / conc

        output_data.add(
            group_id,
            data_type,
            results.shape,
            **kwargs,
        )
        output_data[group_id][...] = post_func(results)
        if scaling_factor:
            output_data[group_id].scaling_factor = conc


def add_grouped_totals_2D(
    trajectory: Trajectory,
    output_data: OutputData,
    result_name: str,
    data_type: str,
    conc_exp: float = 1.0,
    *,
    intra: bool = False,
    scaling_factor: bool = True,
    post_func: Callable[[npt.NDArray], npt.NDArray] = lambda x: x,
    post_label: str = "total",
    **kwargs,
):
    """Add the grouped totals to the output data.

    Parameters
    ----------
    trajectory: Trajectory
        Current state of the trajectory, including selection and transmutation
    output_data : dict[str, npt.NDArray]
        Dictionary of data arrays containing analysis results.
    result_name : str
        The name of the results.
    data_type : str
        The plotting type of the data.
    conc_exp : float
        The exponent the at the product of the concentrations are taken
        to (e.g. (c_i * c_j)**0.5 which is used for DCSF jobs).
    intra: bool
        Add total results for intra results.
    scaling_factor: bool
        Add the scaling factor to the output data if True.
    post_func: Callable[[npt.NDArray], npt.NDArray]
        A function which is applied to the results.
    post_label: str
        The label to be added for grouped summed results.
    """
    tot_n_atms = len(trajectory.atom_indices)

    if intra:
        for grp in trajectory.group_lookup:
            eles = sorted(
                {
                    trajectory.atom_types[x]
                    for cluster in trajectory.chemical_system._clusters[grp]
                    for x in cluster
                    if x in trajectory.atom_indices
                }
            )
            conc = (trajectory.group_lookup[grp] / tot_n_atms) ** conc_exp
            labels = [
                ((grp, *pair), "") for pair in it.combinations_with_replacement(eles, 2)
            ]

            results = (
                weighted_sum(output_data, result_name + "/<%s>/%s%s", labels) / conc
            )

            group_id = GROUP_TEMPLATE.format(result_name, grp, post_label)

            output_data.add(
                group_id,
                data_type,
                results.shape,
                **kwargs,
            )
            output_data[group_id][...] = post_func(results)
            if scaling_factor:
                output_data[group_id].scaling_factor = conc
        return

    for grp_i, grp_j in it.combinations_with_replacement(trajectory.group_lookup, 2):
        eles_i = sorted(
            {
                trajectory.atom_types[x]
                for cluster in trajectory.chemical_system._clusters[grp_i]
                for x in cluster
                if x in trajectory.atom_indices
            }
        )
        eles_j = sorted(
            {
                trajectory.atom_types[x]
                for cluster in trajectory.chemical_system._clusters[grp_j]
                for x in cluster
                if x in trajectory.atom_indices
            }
        )
        conc_i = trajectory.group_lookup[grp_i] / tot_n_atms
        conc_j = trajectory.group_lookup[grp_j] / tot_n_atms
        conc = (conc_i * conc_j) ** conc_exp
        if grp_i != grp_j:
            # for the cross terms we divide by 2 since f(q,t)_OH
            # includes only OH or HO, it gets summed to the total
            # properly by the weight scheme. Similarly, we will
            # have a factor of two in the scaling factor for the
            # cross terms of the molecular case.
            conc *= 2

        if grp_i == grp_j:
            iterable = it.combinations_with_replacement(eles_i, 2)
        else:
            iterable = it.product(eles_i, eles_j)
        labels = [((grp_i, grp_j, *pair), "") for pair in iterable]

        results = (
            weighted_sum(output_data, result_name + "/<%s><%s>/%s%s", labels) / conc
        )

        group_id = PAIR_GROUP_TEMPLATE.format(result_name, grp_i, grp_j, post_label)

        output_data.add(
            group_id,
            data_type,
            results.shape,
            **kwargs,
        )
        output_data[group_id][...] = post_func(results)
        if scaling_factor:
            output_data[group_id].scaling_factor = conc


def label_pairs(labels: Iterable[str], *, all_pairs: bool) -> list[tuple[str, str]]:
    """
    Parameters
    ----------
    labels : Iterable[str]
        List of labels.
    all_pairs : bool
        Return all pairs if true or only the unique pairs if false.

    Returns
    -------
    list[tuple[str, str]]
        A list of label pairs.
    """
    if all_pairs:
        iterable = it.product(sorted(labels), repeat=2)
    else:
        iterable = it.combinations_with_replacement(sorted(labels), 2)
    return iterable


def pair_labels(
    trajectory: Trajectory, *, intra: bool = False, all_pairs: bool = False
) -> list[tuple[str, tuple[str, str]]]:
    """Generates pair labels.

    Parameters
    ----------
    trajectory: Trajectory
        Current state of the trajectory, including selection and transmutation
    intra : bool
        Returns the intra label data if true.
    all_pairs : bool
        Returns all pairs of labels e.g. OH and HO.

    Returns
    -------
    list[tuple[str, tuple[str, str]]]
        The labels of the results and the labels of the individual
        atoms in a tuple.
    """
    labels = []

    if trajectory._grouping_level == "atom":
        selected_elements = trajectory.unique_names
        for ele_i, ele_j in label_pairs(selected_elements, all_pairs=all_pairs):
            labels.append((f"{ele_i}{ele_j}", (ele_i, ele_j)))
        return labels

    if intra:
        for grp in trajectory.group_lookup:
            eles = sorted(
                {
                    trajectory.atom_types[index]
                    for cluster in trajectory.chemical_system._clusters[grp]
                    for index in cluster
                    if index in trajectory.atom_indices
                }
            )
            for ele_i, ele_j in label_pairs(eles, all_pairs=all_pairs):
                pair_label = f"<{grp}>/{ele_i}{ele_j}"
                label_i = f"<{grp}>/{ele_i}"
                label_j = f"<{grp}>/{ele_j}"
                labels.append((pair_label, (label_i, label_j)))
        return labels

    for grp_i, grp_j in label_pairs(trajectory.group_lookup, all_pairs=all_pairs):
        eles_i = sorted(
            {
                trajectory.atom_types[index]
                for cluster in trajectory.chemical_system._clusters[grp_i]
                for index in cluster
                if index in trajectory.atom_indices
            }
        )
        eles_j = sorted(
            {
                trajectory.atom_types[index]
                for cluster in trajectory.chemical_system._clusters[grp_j]
                for index in cluster
                if index in trajectory.atom_indices
            }
        )

        if grp_i == grp_j and not all_pairs:
            pairs = it.combinations_with_replacement(eles_i, 2)
        else:
            pairs = it.product(eles_i, eles_j)
        for ele_i, ele_j in pairs:
            pair_label = f"<{grp_i}><{grp_j}>/{ele_i}{ele_j}"
            label_i = f"<{grp_i}>/{ele_i}"
            label_j = f"<{grp_j}>/{ele_j}"
            labels.append((pair_label, (label_i, label_j)))
    return labels


def update_pair_results(
    trajectory: Trajectory,
    calc_func: Callable[[str, str], Iterable[tuple[str, bool, npt.NDArray]]],
    output_data: OutputData,
    all_pairs: bool = False,
):
    """Updates the output data with pair results.

    Parameters
    ----------
    trajectory: Trajectory
        Current state of the trajectory, including selection and transmutation
    calc_func : Callable[[str, str], Iterable[tuple[str, bool, npt.NDArray]]]
        A function which yields the results name, a bool which
        specifies whether it correspond to intermolecular atom
        pairs and the results.
    output_data : OutputData
        The output data object to write the results to.
    all_pairs : bool
        Updates all pairs of labels e.g. OH and HO.
    """
    if trajectory._grouping_level == "atom":
        selected_elements = trajectory.unique_names
        for ele_i, ele_j in label_pairs(selected_elements, all_pairs=all_pairs):
            for name, _, result in calc_func(ele_i, ele_j):
                output_data[f"{name}/{ele_i}{ele_j}"][...] = result
        return

    for grp_i, grp_j in it.combinations_with_replacement(trajectory.group_lookup, 2):
        eles_i = sorted(
            {
                trajectory.atom_types[index]
                for cluster in trajectory.chemical_system._clusters[grp_i]
                for index in cluster
                if index in trajectory.atom_indices
            }
        )
        eles_j = sorted(
            {
                trajectory.atom_types[index]
                for cluster in trajectory.chemical_system._clusters[grp_j]
                for index in cluster
                if index in trajectory.atom_indices
            }
        )
        if grp_i == grp_j and not all_pairs:
            iterable = it.combinations_with_replacement(eles_i, 2)
        else:
            iterable = it.product(eles_i, eles_j)

        for ele_i, ele_j in iterable:
            label_i = f"<{grp_i}>/{ele_i}"
            label_j = f"<{grp_j}>/{ele_j}"
            for name, intra, result in calc_func(label_i, label_j):
                if intra and grp_i != grp_j:
                    continue

                post_label = f"{ele_i}{ele_j}"

                if intra and grp_i == grp_j:
                    group_id = GROUP_TEMPLATE.format(name, grp_i, post_label)
                else:
                    group_id = PAIR_GROUP_TEMPLATE.format(
                        name, grp_i, grp_j, post_label
                    )
                output_data[group_id][...] = result
