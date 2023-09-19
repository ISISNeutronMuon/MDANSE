# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/MoleculeIndex.py
# @brief     Implements module/class/test MoleculeIndex
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Framework.Selectors.ISelector import ISelector


class MoleculeIndex(ISelector):
    section = "molecules"

    def __init__(self, chemicalSystem: ChemicalSystem):
        ISelector.__init__(self, chemicalSystem)

        self._choices.extend(range(len(self._chemicalSystem.chemical_entities)))

    def select(self, values):
        """Returns the atoms that matches a given list of molecule indexes.

        @param indexes: the molecule indexes list.
        @type indexes: list
        """

        sel = set()

        if "*" in values:
            sel.update([at for at in self._chemicalSystem.atom_list])

        else:
            vals = set([int(v) for v in values])

            ceList = self._chemicalSystem.chemical_entities

            sel.update([at for v in vals for at in ceList[v].atom_list])

        return sel


REGISTRY["molecule_index"] = MoleculeIndex
