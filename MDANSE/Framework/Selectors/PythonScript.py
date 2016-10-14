#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 27, 2015

:author: Eric C. Pellegrini
'''

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
