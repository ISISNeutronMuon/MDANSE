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
import wx.aui as wxaui

from MDANSE import LOGGER, REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin

class UserDefinitionPlugin(ComponentPlugin):
    
    category = ('User definition',)
    
    def __init__(self,parent,*args,**kwargs):
        
        ComponentPlugin.__init__(self,parent,*args,**kwargs)
        
        self.add_ud_panel()
        
        self._mgr.AddPane(self._mainPanel, wxaui.AuiPaneInfo().DestroyOnClose().Center().Dock().CaptionVisible(False).CloseButton(False).BestSize(self.GetSize()))

        self._mgr.Update()
                                
    def add_ud_panel(self):

        udPanel = wx.Panel(self._mainPanel,wx.ID_ANY)
                
        sb = wx.StaticBox(udPanel, wx.ID_ANY)
        actionsSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
                        
        self._udName = wx.TextCtrl(udPanel, wx.ID_ANY, style = wx.TE_PROCESS_ENTER)
        saveButton  = wx.Button(udPanel, wx.ID_ANY, label="Save")
        
        actionsSizer.Add(self._udName, 1, wx.ALL|wx.EXPAND, 5)
        actionsSizer.Add(saveButton, 0, wx.ALL, 5)
        
        udPanel.SetSizer(actionsSizer)
        
        self._mainPanel.GetSizer().Add(udPanel,0,wx.EXPAND|wx.ALL,5)

        self.Bind(wx.EVT_BUTTON, lambda evt : self.on_save(evt), saveButton)
                        
    def on_save(self, event):

        name = str(self._udName.GetValue().strip())
        
        if not name:
            LOGGER('Empty user definition name.','error',['dialog'])
            return

        value = self.validate()        
        if value is None:
            return
                                
        if UD_STORE.has_definition(self._target,self._type,name):
            LOGGER('There is already an user-definition with that name.','error',['dialog'])
            return
                          
        UD_STORE.set_definition(self._target,self._type,name,value)
                 
        PUBLISHER.sendMessage("msg_set_ud",message=None)
                
        UD_STORE.save()

        LOGGER('User definition %r successfully set.' % name,'info',['console'])

REGISTRY["user_definition"] = UserDefinitionPlugin
