# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/SulphurHydrogen.py
# @brief     Implements module/class/test SulphurHydrogen
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


class SulphurHydrogen(ISelector):
    section = "hydrogens"

    def __init__(self, chemical_system: ChemicalSystem):
        
        ISelector.__init__(self, chemical_system)

        for ce in self._chemicalSystem.chemical_entities:
                                        
            sulphurs = [at for at in ce.atom_list if at.element.strip().lower() in ['sulphur', 'sulfur']]
            
            for sul in sulphurs:
                neighbours = sul.bonds
                hydrogens = [neigh.full_name.strip() for neigh in neighbours if neigh.element.strip().lower() == 'hydrogen']
                self._choices.extend(sorted(hydrogens))

    def select(self, names):
        sel = set()

        if "*" in names:
            if len(self._choices) == 1:
                return sel
            names = self._choices[1:]

        vals = set([v.lower() for v in names])
        sel.update([at for at in self._chemicalSystem.atom_list if at.full_name.strip() in vals])
        
        return sel


REGISTRY["sulphur_hydrogen"] = SulphurHydrogen
