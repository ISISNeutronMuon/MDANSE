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
Created on Jun 30, 2015

:author: Eric C. Pellegrini
'''

from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Widgets.UserDefinitionWidget import UserDefinitionWidget, UserDefinitionDialog

class AtomListWidget(UserDefinitionWidget):
    
    type = 'atoms_list'

    def on_new_user_definition(self,event):

        dlg = UserDefinitionDialog(self,self._trajectory,self.type)
        
        dlg.plugin.set_natoms(self._configurator._nAtoms)
                
        dlg.plugin.enable_natoms_selection(False)
        
        dlg.ShowModal()
        
    def msg_set_ud(self):
         
        uds = UD_STORE.filter(self._basename, self.type)
                                
        uds = [v for v in uds if UD_STORE.get_definition(self._basename, self.type,v)["natoms"]==self._configurator._nAtoms] 
        
        self._availableUDs.SetItems(uds)
        