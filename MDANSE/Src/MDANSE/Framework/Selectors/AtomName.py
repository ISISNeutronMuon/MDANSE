# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/AtomName.py
# @brief     Implements module/class/test AtomName
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Framework.Selectors.ISelector import ISelector


class AtomName(ISelector):
    section = "atoms"

    def __init__(self, chemicalSystem: ChemicalSystem):
        ISelector.__init__(self, chemicalSystem)

        self._choices.extend(
            sorted(set([at.name.strip() for at in self._chemicalSystem.atom_list]))
        )

    def select(self, names):
        """Returns the atoms that matches a given list of atom types.

        @param types: the atom types list.
        @type types: list
        """

        sel = set()

        if "*" in names:
            sel.update([at for at in self._chemicalSystem.atom_list])

        else:
            vals = set([v for v in names])
            sel.update(
                [at for at in self._chemicalSystem.atom_list if at.name.strip() in vals]
            )

        return sel
