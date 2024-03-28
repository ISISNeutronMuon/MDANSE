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
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms

LEVELS = collections.OrderedDict()
LEVELS["atom"] = {
    "atom": 0,
    "atomcluster": 0,
    "molecule": 0,
    "nucleotidechain": 0,
    "peptidechain": 0,
    "protein": 0,
}
LEVELS["residue"] = {
    "atom": 0,
    "atomcluster": 1,
    "molecule": 1,
    "nucleotidechain": 1,
    "peptidechain": 1,
    "protein": 1,
}
LEVELS["chain"] = {
    "atom": 0,
    "atomcluster": 1,
    "molecule": 1,
    "nucleotidechain": 2,
    "peptidechain": 2,
    "protein": 2,
}
LEVELS["molecule"] = {
    "atom": 0,
    "atomcluster": 1,
    "molecule": 1,
    "nucleotidechain": 2,
    "peptidechain": 2,
    "protein": 2,
}


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

        if choices is None:
            choices = list(LEVELS.keys())
        else:
            choices = list(set(LEVELS.keys()).intersection(choices))

        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)

    def configure(self, value):
        """
        :param value: the level of granularity at which the atoms should be grouped
        :type value: str
        """

        if value is None:
            value = "atom"

        value = str(value)

        SingleChoiceConfigurator.configure(self, value)

        if value == "atom":
            return

        trajConfig = self._configurable[self._dependencies["trajectory"]]
        atomSelectionConfig = self._configurable[self._dependencies["atom_selection"]]

        allAtoms = sorted_atoms(trajConfig["instance"].chemical_system.atom_list)

        groups = collections.OrderedDict()
        for i in range(atomSelectionConfig["selection_length"]):
            idx = atomSelectionConfig["indexes"][i][0]
            el = atomSelectionConfig["elements"][i][0]
            mass = atomSelectionConfig["masses"][i][0]
            at = allAtoms[idx]
            lvl = LEVELS[value][at.top_level_chemical_entity.__class__.__name__.lower()]
            parent = self.find_parent(at, lvl)
            d = groups.setdefault(parent, {})
            d.setdefault("indexes", []).append(idx)
            d.setdefault("elements", []).append(el)
            d.setdefault("masses", []).append(mass)

        indexes = []
        elements = []
        masses = []
        names = []
        for i, v in enumerate(groups.values()):
            names.append("group_%d" % i)
            elements.append(v["elements"])
            indexes.append(v["indexes"])
            masses.append(v["masses"])

        atomSelectionConfig["indexes"] = indexes
        atomSelectionConfig["elements"] = elements
        atomSelectionConfig["masses"] = masses
        atomSelectionConfig["names"] = names
        atomSelectionConfig["selection_length"] = len(names)
        atomSelectionConfig["unique_names"] = sorted(set(atomSelectionConfig["names"]))

        self["level"] = value

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

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str
        """

        return "Grouping level: %r\n" % self["value"]
