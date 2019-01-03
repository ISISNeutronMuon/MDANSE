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
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import glob
import os

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Selectors.ISelector import ISelector
                
class PythonScript(ISelector):
        
    section = 'miscellaneous'
    
    def __init__(self, trajectory):
        
        ISelector.__init__(self,trajectory)
                
        self._choices.extend(glob.glob(os.path.dirname(PLATFORM.get_path(trajectory.filename)),'*.py'))
        
        self._rindexes = dict([(at.index,at) for at in self._universe.atomList()])
    
    def select(self, scripts):
        
        sel = set()

        if '*' in scripts:
            scripts = self._choices[1:]
                                
        for s in scripts:
            
            namespace = {"universe" : self._universe}
        
            try:
                execfile(s,namespace)
            # Any kind of error that may occur in the script must be caught 
            except:
                continue
            else:
                if not namespace.has_key("selection"):
                    continue
                                
                sel.update([self._rindexes[idx] for idx in namespace["selection"]])
                                        
        return sel
    
REGISTRY["python_script"] = PythonScript
