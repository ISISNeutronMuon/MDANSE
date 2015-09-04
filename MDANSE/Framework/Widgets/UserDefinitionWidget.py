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
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

import abc
import os

import wx
import wx.aui as wxaui

from MDANSE import LOGGER, REGISTRY
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.Plugins.ComponentPlugin import ComponentPlugin
from MDANSE.Framework.UserDefinitionsStore import UD_STORE
from MDANSE.Framework.Widgets.IWidget import IWidget
from MDANSE.GUI import DATA_CONTROLLER

class UserDefinitionsPanel(wx.Panel):
    
    def __init__(self,udType,*args,**kwargs):

        wx.Panel.__init__(self,*args,**kwargs)

        self._udType = udType
                
        sb = wx.StaticBox(self, wx.ID_ANY)
        actionsSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
                        
        cancelButton  = wx.Button(self, wx.ID_ANY, label="Cancel")
        self._udName = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_PROCESS_ENTER)
        saveButton  = wx.Button(self, wx.ID_ANY, label="Save")
        
        actionsSizer.Add(cancelButton, 0, wx.ALL, 5)
        actionsSizer.Add(self._udName, 1, wx.ALL|wx.EXPAND, 5)
        actionsSizer.Add(saveButton, 0, wx.ALL, 5)
        
        self.SetSizer(actionsSizer)
                
        self._validator = None
                 
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_BUTTON, self.on_close, cancelButton)
        self.Bind(wx.EVT_BUTTON, self.on_save, saveButton)

    def set_validator(self,validator):
        
        self._validator = validator

    def validate(self):
        
        if self._validator is not None:
            return self._validator()
        else:
            return None
        
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
                
        if UD_STORE.has_definition(self._target,self.type,name):
            LOGGER('There is already a user-definition that matches %s,%s,%s' % (self._target,self.type,name),'error',['dialog'])
            self.EndModal(wx.ID_CANCEL)
            return
                  
        UD_STORE.set_definition(self._target,self.type,name,value)
        UD_STORE.save()
                 
        pub.sendMessage("msg_save_definition", message = (self._target, self.type, name))
                         
        self.EndModal(wx.ID_OK)
                
    def on_close(self, event):
        
        self.EndModal(wx.ID_CANCEL)

class UserDefinitionsDialog(wx.Dialog):
    
    __metaclass__ = abc.ABCMeta

    def __init__(self, parent, target, *args, **kwargs):
        
        wx.Dialog.__init__(self, parent, *args, **kwargs)

        self._parent = parent
        
        self._target = target
        
        self._mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self._ud = {}
                                                                
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
                
        if UD_STORE.has_definition(self._target,self.type,name):
            LOGGER('There is already a user-definition that matches %s,%s,%s' % (self._target,self.type,name),'error',['dialog'])
            self.EndModal(wx.ID_CANCEL)
            return
                  
        UD_STORE.set_definition(self._target,self.type,name,value)
        UD_STORE.save()
                 
        pub.sendMessage("msg_save_definition", message = (self._target, self.type, name))
                         
        self.EndModal(wx.ID_OK)
                
    def on_close(self, event):
        
        self.EndModal(wx.ID_CANCEL)

class UserDefinitionWidget(IWidget):
    
    __metaclass__ = abc.ABCMeta
    
    type = None    
        
    def initialize(self):
        
        self._filename = None
        self._basename = None
        
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._availableUDs = wx.Choice(self._widgetPanel, wx.ID_ANY,style=wx.CB_SORT)
        self._newUD = wx.Button(self._widgetPanel, wx.ID_ANY, label="New")
        sizer.Add(self._availableUDs, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self._newUD, 0, wx.ALL|wx.EXPAND, 5)

        pub.subscribe(self.on_save_definition, ("msg_save_definition",))

        self.Bind(wx.EVT_BUTTON, self.on_new_user_definition, self._newUD)

        return sizer
    
    def on_new_user_definition(self,event):
        
        dlg = UDDialog(self,self._trajectory,self.type)
        
        dlg.ShowModal()
        
    def get_widget_value(self):
        
        return str(self._availableUDs.GetStringSelection())    

    def set_data(self, datakey):

        self._filename = datakey

        self._trajectory = DATA_CONTROLLER[datakey]

        self._basename = os.path.basename(self._filename)
        
        uds = UD_STORE.filter(self._basename, self.type)
        
        self._availableUDs.SetItems(uds)

    def on_save_definition(self, message):
         
        filename, section, name = message
         
        if section is not self.type:
            return
         
        if filename != self._basename:
            return
        
        self._availableUDs.Append(name)

class UDDialog(wx.Dialog):
    
    def __init__(self,parent,trajectory,udType,*args,**kwargs):

        wx.Dialog.__init__(self, parent)
        
        self._mgr = wxaui.AuiManager(self)

        self.datakey = trajectory.filename
         
        self._plugin = REGISTRY['plugin'][udType](self,*args,**kwargs)
        
        self.SetTitle(self._plugin.label)
        
        self._plugin.set_trajectory(trajectory)
                
        pub.sendMessage("msg_set_data", plugin=self._plugin)
        
        self.Bind(wx.EVT_CLOSE, self.on_quit)

    def on_quit(self, event):
        
        d = wx.MessageDialog(None,'Do you really want to quit ?','Question',wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()           

    @property
    def plugin(self):
        
        return self._plugin

class UDPlugin(ComponentPlugin):
    
    def __init__(self,parent,*args,**kwargs):
        
        ComponentPlugin.__init__(self,parent,size=(800,500))
        
        self.add_ud_panel()
                
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

        self.Bind(wx.EVT_BUTTON, self.on_save, saveButton)

    def on_save(self, event):

        name = str(self._udName.GetValue().strip())
        
        if not name:
            LOGGER('Empty user definition name.','error',['dialog'])
            return

        value = self.validate()        
        if value is None:
            return 
                
        if UD_STORE.has_definition(self._target,self.type,name):
            LOGGER('There is already a user-definition that matches %s,%s,%s' % (self._target,self.type,name),'error',['dialog'])
            self.EndModal(wx.ID_CANCEL)
            return
                  
        UD_STORE.set_definition(self._target,self.type,name,value)
        UD_STORE.save()
                 
        pub.sendMessage("msg_save_definition", message=(self._target,self.type,name))
