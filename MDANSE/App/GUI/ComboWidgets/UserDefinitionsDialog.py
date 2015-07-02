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
Created on Apr 14, 2015

:author: Eric C. Pellegrini
'''

import abc

import wx

from MDANSE import LOGGER
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.UserDefinitionsStore import UD_STORE

class UserDefinitionsDialog(wx.Dialog):
    
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent, target, section, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, *args, **kwargs)

        self._parent = parent
        
        self._target = target
        
        self._section = section

        self._ud = {}

        self._mainSizer = wx.BoxSizer(wx.VERTICAL)
                                
        self.build_dialog()

        udPanel = wx.Panel(self,wx.ID_ANY)
                
        sb = wx.StaticBox(udPanel, wx.ID_ANY)
        actionsSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
                        
        cancelButton  = wx.Button(udPanel, wx.ID_ANY, label="Cancel")
        self._udName = wx.TextCtrl(udPanel, wx.ID_ANY, style = wx.TE_PROCESS_ENTER)
        saveButton  = wx.Button(udPanel, wx.ID_ANY, label="Save")
        
        actionsSizer.Add(cancelButton, 0, wx.ALL, 5)
        actionsSizer.Add(self._udName, 1, wx.ALL|wx.EXPAND, 5)
        actionsSizer.Add(saveButton, 0, wx.ALL, 5)
        
        udPanel.SetSizer(actionsSizer)
                 
        self._mainSizer.Add(udPanel,0,wx.EXPAND|wx.ALL,5)
        
        self.SetSizer(self._mainSizer)            

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_BUTTON, self.on_close, cancelButton)
        self.Bind(wx.EVT_BUTTON, self.on_save, saveButton)

    @abc.abstractmethod
    def build_dialog(self):
        pass
        
    @abc.abstractmethod
    def validate(self):
        pass

    def getUserDefinitionName(self):
        
        return str(self._udName.GetValue())

    def on_save(self, event):

        name = str(self._udName.GetValue().strip())
         
        if not name:
            LOGGER('Empty user definition name.','error',['dialog'])
            return

        value = self.validate()        
        if value is None:
            return 
                
        if UD_STORE.has_definition(self._target,self._section,name):
            LOGGER('There is already a user-definition that matches %s,%s,%s' % (self._target,self._section,name),'error',['dialog'])
            self.EndModal(wx.ID_CANCEL)
            return
                  
        UD_STORE.set_definition(self._target,self._section,name,value)
        UD_STORE.save()
                 
        pub.sendMessage("save_definition", message = (self._target, name))
                         
        self.EndModal(wx.ID_OK)
                
    def on_close(self, event):
        
        self.EndModal(wx.ID_CANCEL)
