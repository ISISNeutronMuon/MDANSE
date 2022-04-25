# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Selectors/PythonScript.py
# @brief     Implements module/class/test PythonScript
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import glob
import os

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
                
class PythonScript(ISelector):
        
    section = 'miscellaneous'
        
    def select(self, scripts):
        
        sel = set()

        if '*' in scripts:
            sel.update([at for at in self._chemicalSystem.atom_list()])
                                
        for s in scripts:
            namespace = {"chemicalSystem" : self._chemicalSystem}
        
            try:
                exec(open(s,'r').read(),namespace)
            # Any kind of error that may occur in the script must be caught 
            except:
                continue
            else:
                sel.update(namespace.get("selection",[]))
                                        
        return sel
    
REGISTRY["python_script"] = PythonScript
