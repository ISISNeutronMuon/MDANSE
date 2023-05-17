# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/Within.py
# @brief     Implements module/class/test Within
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
               
class WithinShell(ISelector):

    type = "within_selection"

    section = None

    def select(self, ref, mini=0.0, maxi=1.0):

        sel = set()

        if self._chemicalSystem.configuration is not None:
            sel.update(self._chemicalSystem.configuration.atomsInShell(ref,mini,maxi))
        
        return sel
    
REGISTRY["within_shell"] = WithinShell
