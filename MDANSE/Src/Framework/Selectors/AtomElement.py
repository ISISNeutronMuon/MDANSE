# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/AtomType.py
# @brief     Implements module/class/test AtomType
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


class AtomElement(ISelector):
    section = "atoms"

    def __init__(self, chemicalSystem: ChemicalSystem):
        ISelector.__init__(self, chemicalSystem)

        self._choices.extend(
            sorted(set([at.element.lower() for at in self._chemicalSystem.atom_list]))
        )

    def select(self, elements):
        """Returns the atoms that matches a given list of elements.

        @param elements: the atom elements list.
        @type elements: list
        """

        sel = set()

        if "*" in elements:
            sel.update([at for at in self._chemicalSystem.atom_list])

        else:
            vals = [v.lower() for v in elements]

            if "sulfur" in vals:
                vals.append("sulphur")
            else:
                if "sulphur" in vals:
                    vals.append("sulfur")

            vals = set(vals)

            sel.update(
                [
                    at
                    for at in self._chemicalSystem.atom_list
                    if at.element.strip().lower() in vals
                ]
            )

        return sel


REGISTRY["atom_element"] = AtomElement
