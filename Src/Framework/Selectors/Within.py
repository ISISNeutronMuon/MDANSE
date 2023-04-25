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
               
class WithinSelection(ISelector):

    type = "within_selection"

    section = None

    def select(self, atoms, mini=0.0, maxi=1.0):

        sel = set()

        for at in atoms:
            sel.update([a for a in self._universe.selectShell(at.position(),mini,maxi).atomList()])
        
        return sel
    
REGISTRY["within_selection"] = WithinSelection
