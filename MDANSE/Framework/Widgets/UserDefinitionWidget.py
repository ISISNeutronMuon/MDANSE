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

class UserDefinitionWidget(IWidget):
    
    __metaclass__ = abc.ABCMeta
    
    type = None    
                
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._availableUDs = wx.Choice(self._widgetPanel, wx.ID_ANY,style=wx.CB_SORT)
        viewUD = wx.Button(self._widgetPanel, wx.ID_ANY, label="View selected definition")
        newUD = wx.Button(self._widgetPanel, wx.ID_ANY, label="New definition")
        sizer.Add(self._availableUDs, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(viewUD, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(newUD, 0, wx.ALL|wx.EXPAND, 5)

        pub.subscribe(self.msg_set_ud, "msg_set_ud")

        self.Bind(wx.EVT_BUTTON, self.on_view_user_definition, viewUD)
        self.Bind(wx.EVT_BUTTON, self.on_new_user_definition, newUD)

        return sizer
    
    def on_view_user_definition(self,event):
        
        ud = self._availableUDs.GetStringSelection()
        if not ud:
            LOGGER("Please select a user definition","error",["dialog"])
            return
        
        from MDANSE.Framework.Plugins.UserDefinitionViewerPlugin import UserDefinitionViewerFrame
        
        f = UserDefinitionViewerFrame(self,ud=[self._basename,self.type,ud])
        
        f.Show()
    
    def on_new_user_definition(self,event):
        
        dlg = UserDefinitionsDialog(self,self._trajectory,self.type)
        
        dlg.ShowModal()
        
    def get_widget_value(self):
        
        return str(self._availableUDs.GetStringSelection())    

    def set_data(self, datakey):

        self._filename = datakey

        self._trajectory = DATA_CONTROLLER[datakey]

        self._basename = os.path.basename(self._filename)
        
        self.msg_set_ud()
        
        uds = UD_STORE.filter(self._basename, self.type)
        
        self._availableUDs.SetItems(uds)

    def msg_set_ud(self):
         
        uds = UD_STORE.filter(self._basename, self.type)
        
        self._availableUDs.SetItems(uds)

class UserDefinitionsDialog(wx.Dialog):
    
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

class UserDefinitionsPlugin(ComponentPlugin):
    
    category = ('User definition',)
    
    def __init__(self,parent,*args,**kwargs):
        
        ComponentPlugin.__init__(self,parent,size=(800,500))
        
        self.add_ud_panel()
                
    def add_ud_panel(self):

        udPanel = wx.Panel(self._mainPanel,wx.ID_ANY)
                
        sb = wx.StaticBox(udPanel, wx.ID_ANY)
        actionsSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
                        
        self._udName = wx.TextCtrl(udPanel, wx.ID_ANY, style = wx.TE_PROCESS_ENTER)
        saveButton  = wx.Button(udPanel, wx.ID_ANY, label="Set")
        
        actionsSizer.Add(self._udName, 1, wx.ALL|wx.EXPAND, 5)
        actionsSizer.Add(saveButton, 0, wx.ALL, 5)
        
        udPanel.SetSizer(actionsSizer)
        
        self._mainPanel.GetSizer().Add(udPanel,0,wx.EXPAND|wx.ALL,5)

        self.Bind(wx.EVT_BUTTON, self.on_set_ud, saveButton)

    def on_set_ud(self, event):

        name = str(self._udName.GetValue().strip())
        
        if not name:
            LOGGER('Empty user definition name.','error',['console'])
            return

        value = self.validate()        
        if value is None:
            return 
                
        if UD_STORE.has_definition(self._target,self.type,name):
            LOGGER('There is already a user-definition that matches %s,%s,%s' % (self._target,self.type,name),'error',['console'])
            return
                  
        UD_STORE.set_definition(self._target,self.type,name,value)
                 
        pub.sendMessage("msg_set_ud")

        LOGGER('User definition %r successfully set.' % name,'info',['console'])
