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


from MDANSE.Framework.Configurators.SingleChoiceConfigurator import (
    SingleChoiceConfigurator,
)


class GroupingLevelConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to choose the level of granularity in the atom selection.

    When reading the trajectory, the level of granularity will be applied by grouping the atoms of the selection
    to a single dummy-atoms located on the center of gravity of those atoms.

    The level of granularity currently supported are:

    * 'atom': no grouping will be performed
    * 'group': the atoms that belongs to an AtomCluster object will be grouped as a single atom per object while the ones that belongs to a Molecule, NucleotideChain, PeptideChain and Protein object will be grouped according to the chemical group they belong to (e.g. peptide group, methyl group ...)
    * 'residue': the atoms that belongs to anAtomCluster or Molecule object will be grouped as a single atom per object while the ones thta belongs to a NucleotideChain, PeptideChain or Protein object will be grouped according to the residue to which they belong to (e.g. Histidine, Cytosyl ...)
    * 'chain': the atoms that belongs to an AtomCluster or Molecule object will be grouped as a single atom per object while the ones that belongs to a NucleotideChain, PeptideChain or Protein object will be grouped according to the chain they belong to
    * 'molecule': the atoms that belongs to any chemical entity will be grouped as a single atom per object
    """

    _default = "atom"

    def __init__(self, name, choices=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration
        :type name: str
        :param choices: the level of granularities allowed for the input value. If None all levels are allowed.
        :type choices: one of ['atom','group','residue','chain','molecule'] or None
        """
        usual_choices = ["atom", "molecule", "group"]

        if choices is None:
            choices = usual_choices
        else:
            choices += [x for x in usual_choices if x not in choices]

        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)

    def configure(self, value):
        """
        :param value: the level of granularity at which the atoms should be grouped
        :type value: str
        """
        self._original_input = value

        if value is None:
            value = "atom"

        value = str(value)

        SingleChoiceConfigurator.configure(self, value)

        if value == "atom":
            return
        trajConfig = self._configurable[self._dependencies["trajectory"]]
        atomSelectionConfig = self._configurable[self._dependencies["atom_selection"]]
        chemical_system = trajConfig["instance"].chemical_system
        indices = []
        elements = []
        names = []
        masses = []
        mass_lookup = chemical_system.atom_property("atomic_weight")

        if value == "molecule":
            for mol_name in chemical_system._clusters.keys():
                for mol_number, cluster in enumerate(
                    chemical_system._clusters[mol_name]
                ):
                    indices.append(cluster)
                    elements.append([chemical_system.atom_list[x] for x in cluster])
                    names.append(f"{mol_name}_mol{mol_number + 1}")
                    masses.append([mass_lookup[x] for x in cluster])
        elif value == "group":
            for group_name, group_indices in chemical_system._labels.items():
                residue = set(group_indices)
                counter = 1
                for clustername, clusterlist in chemical_system._clusters.items():
                    for cluster in clusterlist:
                        molecule = set(cluster)
                        if molecule.issubset(residue) or residue.issubset(molecule):
                            indices.append(list(molecule.intersection(residue)))
                            elements.append(
                                [chemical_system.atom_list[x] for x in cluster]
                            )
                            names.append(f"{group_name}_num{counter}_in_{clustername}")
                            masses.append([mass_lookup[x] for x in cluster])
                            counter += 1

        atomSelectionConfig["indices"] = indices
        atomSelectionConfig["elements"] = elements
        atomSelectionConfig["masses"] = masses
        atomSelectionConfig["names"] = names
        atomSelectionConfig["selection_length"] = len(names)
        atomSelectionConfig["unique_names"] = sorted(set(atomSelectionConfig["names"]))

        self["level"] = value
        self["group_indices"] = list(range(len(names)))
        if atomSelectionConfig["selection_length"] == 0:
            self.error_status = "This option resulted in nothing being selected in the current trajectory"

    @staticmethod
    def find_parent(atom, level):
        """
        Retrieve recursively the parent of a given atom at a given level.
        For example, a level of 1 will return the direct parent of the atom.

        :note: this is a static method

        :param atom: the atom for which the parent is searched for
        :type atom: Atom object
        :param level: the level of the parent
        :type level: int
        """

        for _ in range(level):
            atom = atom.parent

        return atom
