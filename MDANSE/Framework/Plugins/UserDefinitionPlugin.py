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
Created on Sep 22, 2015

@author: pellegrini
'''

import wx

from MDANSE import LOGGER
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.Plugins.ComponentPlugin import ComponentPlugin
from MDANSE.Framework.UserDefinitionStore import UD_STORE

class UserDefinitionPlugin(ComponentPlugin):
    
    category = ('User definition',)
    
    def __init__(self,parent,*args,**kwargs):
        
        ComponentPlugin.__init__(self,parent,size=(800,500))
        
        self.add_ud_panel()
                
    def add_ud_panel(self):

        udPanel = wx.Panel(self._mainPanel,wx.ID_ANY)
                
        sb = wx.StaticBox(udPanel, wx.ID_ANY)
        actionsSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
                        
        self._udName = wx.TextCtrl(udPanel, wx.ID_ANY, style = wx.TE_PROCESS_ENTER)
        applyButton  = wx.Button(udPanel, wx.ID_ANY, label="Apply")
        saveButton  = wx.Button(udPanel, wx.ID_ANY, label="Save")
        
        actionsSizer.Add(self._udName, 1, wx.ALL|wx.EXPAND, 5)
        actionsSizer.Add(applyButton, 0, wx.ALL, 5)
        actionsSizer.Add(saveButton, 0, wx.ALL, 5)
        
        udPanel.SetSizer(actionsSizer)
        
        self._mainPanel.GetSizer().Add(udPanel,0,wx.EXPAND|wx.ALL,5)

        self.Bind(wx.EVT_BUTTON, self.on_apply, applyButton)
        self.Bind(wx.EVT_BUTTON, lambda evt : self.on_apply(evt,True), saveButton)
                        
    def on_apply(self, event, save=False):

        name = str(self._udName.GetValue().strip())
        
        if not name:
            LOGGER('Empty user definition name.','error',['dialog'])
            return

        value = self.validate()        
        if value is None:
            return
                        
        if UD_STORE.has_definition(self._target,self.type,name):
            LOGGER('There is already a user-definition with that name.','error',['dialog'])
            return
                  
        UD_STORE.set_definition(self._target,self.type,name,value)
                 
        pub.sendMessage("msg_set_ud")
        
        LOGGER('User definition %r successfully set.' % name,'info',['console'])
        
        if save:
            UD_STORE.save()
