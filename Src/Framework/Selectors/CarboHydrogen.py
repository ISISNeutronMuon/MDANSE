# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/CarboHydrogen.py
# @brief     Implements module/class/test CarboHydrogen
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
    
class CarboHydrogen(ISelector):
        
    section = "hydrogens"

    def __init__(self, chemicalSystem):
        
        ISelector.__init__(self,chemicalSystem)

        for ce in self._chemicalSystem.chemical_entities:
                                        
            carbons = [at for at in ce.atom_list() if at.element.strip().lower() == 'carbon']

            for car in carbons:
                neighbours = car.bonds
                hydrogens = [neigh.full_name().strip() for neigh in neighbours if neigh.element.strip().lower() == 'hydrogen']
                self._choices.extend(sorted(hydrogens))


    def select(self, names):
    
        sel = set()

        if '*' in names:
            names = self._choices[1:]
            
        vals = set([v for v in names])
        sel.update([at for at in self._chemicalSystem.atom_list() if at.full_name().strip() in vals])
        
        return sel
    
REGISTRY["carbo_hydrogen"] = CarboHydrogen
