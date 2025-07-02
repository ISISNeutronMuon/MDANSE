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
import itertools as it
from collections.abc import Iterable
from typing import Callable, Optional

import numpy.typing as npt
from more_itertools import collapse

from MDANSE.Framework.Configurators.SingleChoiceConfigurator import (
    SingleChoiceConfigurator,
)
from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData
from MDANSE.Mathematics.Arithmetic import weighted_sum


class GroupingLevelConfigurator(SingleChoiceConfigurator):
    """Define how the partial results will be grouped in the output.

    The grouping levels currently supported are:
    * 'atom': no changes are made to the atom selection
    * 'each atom': no changes are made to the atom selection
    * 'molecule': this changes the atom names in the atom selection so that
        it includes the molecule name that they are a part of e.g. <H2_O1>/H
        for a water molecule's hydrogen atom. Job in mdanse will sum results
        based on the atom names so that results like f(q,t)/<H2_O1>/H will
        be obtained.
    * 'each molecule': this changes the atom selection so that the atom
        indices for each molecule will be grouped together. Jobs can
        then run calculations can be run for each group of indices
        together.
    """

    GROUP_TEMPLATE = "{}/<{}>/{}"
    PAIR_GROUP_TEMPLATE = "{}/<{}><{}>/{}"

    _default = "atom"

    def __init__(self, name: str, choices: Optional[list[str]] = None, **kwargs):
        """
        Parameters
        ----------
        name : str
            The name of the configurator.
        choices : Optional[list[str]]
            The grouping choices allowed for the job that will be
            configured.
        """
        usual_choices = ["atom", "molecule"]

        if choices is None:
            choices = usual_choices

        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)

    def configure(self, value: str):
        """
        Parameters
        ----------
        value : str
            The level of granularity at which the atoms should be grouped
        """
        self._original_input = value

        if value is None:
            value = "atom"

        value = str(value)

        SingleChoiceConfigurator.configure(self, value)

        self["level"] = value

        trajConfig = self.configurable[self.dependencies["trajectory"]]
        atomSelectionConfig = self.configurable[self.dependencies["atom_selection"]]
        chemical_system = trajConfig["instance"].chemical_system

        if value in {"atom", "each atom"}:
            return

        indices = []
        elements = []
        names = []
        all_elements = []
        all_names = []
        masses = []
        group_names = []
        group_elements = {}
        group_n_atms = {}
        mass_lookup = chemical_system.atom_property("atomic_weight")

        if value == "molecule":
            if len(trajConfig["instance"].chemical_system.unique_molecules()) == 0:
                self.error_status = "The trajectory does not contain molecules."
                return

            for mol_name in chemical_system._clusters:
                n_atms = 0
                group_name_elements = []
                mol_selected = False
                for mol_number, cluster in enumerate(
                    chemical_system._clusters[mol_name]
                ):
                    for x in cluster:
                        all_elements.append([chemical_system.atom_list[x]])
                        all_names.append(f"<{mol_name}>/{chemical_system.atom_list[x]}")
                        if x not in atomSelectionConfig["flatten_indices"]:
                            continue
                        mol_selected = True
                        indices.append([x])
                        elements.append([chemical_system.atom_list[x]])
                        group_name_elements.append(chemical_system.atom_list[x])
                        names.append(f"<{mol_name}>/{chemical_system.atom_list[x]}")
                        masses.append([mass_lookup[x]])
                        n_atms += 1
                if mol_selected:
                    group_names.append(mol_name)
                    group_elements[mol_name] = group_name_elements
                    group_n_atms[mol_name] = n_atms

            self["name_to_element"] = {
                name: element[0] for name, element in zip(names, elements)
            }
            self["group_names"] = sorted(set(group_names))
            self["group_elements"] = group_elements
            self["group_n_atms"] = group_n_atms

        elif value == "each molecule":
            for mol_name, clusters in chemical_system._clusters.items():
                for mol_number, cluster in enumerate(clusters):
                    indices.append(cluster)
                    elements.append([chemical_system.atom_list[x] for x in cluster])
                    names.append(f"{mol_name}_mol{mol_number + 1}")
                    masses.append([mass_lookup[x] for x in cluster])

        atomSelectionConfig["indices"] = indices
        atomSelectionConfig["flatten_indices"] = list(collapse(indices))
        atomSelectionConfig["elements"] = elements
        atomSelectionConfig["masses"] = masses
        atomSelectionConfig["names"] = names
        atomSelectionConfig["all_elements"] = all_elements
        atomSelectionConfig["all_names"] = all_names
        atomSelectionConfig["selection_length"] = len(names)
        atomSelectionConfig["unique_names"] = sorted(set(names))

        if atomSelectionConfig["selection_length"] == 0:
            self.error_status = "This option resulted in nothing being selected in the current trajectory"

    def get_element_from_label(self, label: str) -> str:
        """Returns the element for a given label.

        Parameters
        ----------
        label : str
            The label of the element e.g. <H2_O1>/H

        Returns
        -------
        str
            The element of the inputted label.
        """
        if self["level"] == "atom":
            return label
        return self["name_to_element"][label]

    def add_grouped_totals(
        self,
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
        tot_n_atms = self.configurable[self.dependencies["atom_selection"]][
            "selection_length"
        ]

        if self["level"] == "atom":
            return

        if dim == 1:
            for grp in self["group_names"]:
                grp_ele = sorted(set(self["group_elements"][grp]))
                conc = self["group_n_atms"][grp] / tot_n_atms
                labels = [((grp, ele), "") for ele in grp_ele]
                group_id = self.GROUP_TEMPLATE.format(result_name, grp, post_label)

                results = (
                    weighted_sum(output_data, result_name + "/<%s>/%s", labels) / conc
                )

                output_data.add(
                    group_id,
                    data_type,
                    results.shape,
                    **kwargs,
                )
                output_data[group_id][...] = post_func(results)
                if scaling_factor:
                    output_data[group_id].scaling_factor = conc
        elif dim == 2:
            if intra:
                for grp in self["group_names"]:
                    eles = sorted(set(self["group_elements"][grp]))
                    conc = (self["group_n_atms"][grp] / tot_n_atms) ** conc_exp
                    labels = [
                        ((grp, *pair), "")
                        for pair in it.combinations_with_replacement(eles, 2)
                    ]

                    results = (
                        weighted_sum(output_data, result_name + "/<%s>/%s%s", labels)
                        / conc
                    )

                    group_id = self.GROUP_TEMPLATE.format(result_name, grp, post_label)

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

            for grp_i, grp_j in it.combinations_with_replacement(
                self["group_names"], 2
            ):
                eles_i = sorted(set(self["group_elements"][grp_i]))
                eles_j = sorted(set(self["group_elements"][grp_j]))
                conc_i = self["group_n_atms"][grp_i] / tot_n_atms
                conc_j = self["group_n_atms"][grp_j] / tot_n_atms
                if grp_i != grp_j:
                    # for the cross terms we divide by 2 since f(q,t)_OH
                    # includes only OH or HO, it gets summed to the total
                    # properly by the weight scheme. Similarly, we will
                    # have a factor of two in the scaling factor for the
                    # cross terms of the molecular case.
                    conc = 2 * (conc_i * conc_j) ** conc_exp
                else:
                    conc = (conc_i * conc_j) ** conc_exp

                if grp_i == grp_j:
                    iterable = it.combinations_with_replacement(eles_i, 2)
                else:
                    iterable = it.product(eles_i, eles_j)
                labels = [((grp_i, grp_j, *pair), "") for pair in iterable]

                results = (
                    weighted_sum(output_data, result_name + "/<%s><%s>/%s%s", labels)
                    / conc
                )

                group_id = self.PAIR_GROUP_TEMPLATE.format(
                    result_name, grp_i, grp_j, post_label
                )

                output_data.add(
                    group_id,
                    data_type,
                    results.shape,
                    **kwargs,
                )
                output_data[group_id][...] = post_func(results)
                if scaling_factor:
                    output_data[group_id].scaling_factor = conc
        else:
            raise NotImplementedError("Grouped total for dim > 2 not implemented.")

    def pair_labels(
        self, *, intra: bool = False, all_pairs: bool = False
    ) -> list[tuple[str, tuple[str, str]]]:
        """Generates pair labels.

        Parameters
        ----------
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

        if self["level"] == "atom":
            atom_selection = self.configurable[self.dependencies["atom_selection"]]
            selected_elements = atom_selection["unique_names"]
            for ele_i, ele_j in self.label_pairs(
                selected_elements, all_pairs=all_pairs
            ):
                labels.append((f"{ele_i}{ele_j}", (ele_i, ele_j)))
            return labels

        if intra:
            for grp in self["group_names"]:
                eles = sorted(set(self["group_elements"][grp]))
                for ele_i, ele_j in self.label_pairs(eles, all_pairs=all_pairs):
                    pair_label = f"<{grp}>/{ele_i}{ele_j}"
                    label_i = f"<{grp}>/{ele_i}"
                    label_j = f"<{grp}>/{ele_j}"
                    labels.append((pair_label, (label_i, label_j)))
            return labels

        for grp_i, grp_j in self.label_pairs(self["group_names"], all_pairs=all_pairs):
            eles_i = sorted(set(self["group_elements"][grp_i]))
            eles_j = sorted(set(self["group_elements"][grp_j]))

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
        self,
        calc_func: Callable[[str, str], Iterable[tuple[str, bool, npt.NDArray]]],
        output_data: OutputData,
        all_pairs: bool = False,
    ):
        """Updates the output data with pair results.

        Parameters
        ----------
        calc_func : Callable[[str, str], Iterable[tuple[str, bool, npt.NDArray]]]
            A function which yields the results name, a bool which
            specifies whether it correspond to intermolecular atom
            pairs and the results.
        output_data : OutputData
            The output data object to write the results to.
        all_pairs : bool
            Updates all pairs of labels e.g. OH and HO.
        """
        if self["level"] == "atom":
            atom_selection = self.configurable[self.dependencies["atom_selection"]]
            selected_elements = atom_selection["unique_names"]
            for ele_i, ele_j in self.label_pairs(
                selected_elements, all_pairs=all_pairs
            ):
                for name, _, result in calc_func(ele_i, ele_j):
                    output_data[f"{name}/{ele_i}{ele_j}"][...] = result
            return

        for grp_i, grp_j in it.combinations_with_replacement(self["group_names"], 2):
            eles_i = sorted(set(self["group_elements"][grp_i]))
            eles_j = sorted(set(self["group_elements"][grp_j]))
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
                        group_id = self.GROUP_TEMPLATE.format(name, grp_i, post_label)
                    else:
                        group_id = self.PAIR_GROUP_TEMPLATE.format(
                            name, grp_i, grp_j, post_label
                        )
                    output_data[group_id][...] = result

    def label_pairs(
        self, labels: Iterable[str], *, all_pairs: bool
    ) -> list[tuple[str, str]]:
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
            iterable = it.product(labels, repeat=2)
        else:
            iterable = it.combinations_with_replacement(labels, 2)
        return sorted(iterable)
