# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/OxyHydrogen.py
# @brief     Implements module/class/test OxyHydrogen
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


class OxyHydrogen(ISelector):
    section = "hydrogens"

    def __init__(self, chemicalSystem: ChemicalSystem):
        ISelector.__init__(self, chemicalSystem)

        for ce in self._chemicalSystem.chemical_entities:
            oxygens = [
                at for at in ce.atom_list if at.element.strip().lower() == "oxygen"
            ]

            for oxy in oxygens:
                neighbours = oxy.bonds
                hydrogens = [
                    neigh.full_name.strip()
                    for neigh in neighbours
                    if neigh.element.strip().lower() == "hydrogen"
                ]
                self._choices.extend(sorted(hydrogens))

    def select(self, names):
        sel = set()

        if "*" in names:
            names = self._choices[1:]

        vals = set(names)
        sel.update(
            [
                at
                for at in self._chemicalSystem.atom_list
                if at.full_name.strip() in vals
            ]
        )

        return sel


REGISTRY["oxy_hydrogen"] = OxyHydrogen
