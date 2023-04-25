# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/Expression.py
# @brief     Implements module/class/test Expression
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
               
class Expression(ISelector):

    section = None

    def select(self, expression):
                   
        sel = set()
                        
        expression = expression.lower()
        
        aList = self._universe.atomList()
                
        _,_,_ = self._universe.configuration().array.T
                                
        sel.update([aList[idx] for idx in eval(expression)])
        
        return sel

REGISTRY["expression"] = Expression
