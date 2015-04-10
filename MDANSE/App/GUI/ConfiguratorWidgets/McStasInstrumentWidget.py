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

@author: pellegrini
'''

import os
import re
import subprocess

import wx

from MDANSE.Externals.pubsub import pub

from MDANSE.App.GUI.ConfiguratorWidgets.IConfiguratorWidget import IConfiguratorWidget

class McStasInstrumentWidget(IConfiguratorWidget):
    
    type = "mcstas_instrument"
    
    _mcStasTypes = {'double' : float, 'int' : int, 'string' : str}

    def initialize(self):
        pass

    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._instrument = wx.Choice(self._widgetPanel, wx.ID_ANY)
        
        self._browse = wx.Button(self._widgetPanel, wx.ID_ANY, label="Browse")

        sizer.Add(self._instrument, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self._browse, 0, wx.ALL, 5)
        
        self.Bind(wx.EVT_CHOICE, self.on_select_instrument, self._instrument)
        self.Bind(wx.EVT_BUTTON, self.on_browse_instrument, self._browse)
        
        return sizer

    def on_browse_instrument(self, event):
        
        dlg = wx.FileDialog(self, "select instrument executable", os.getcwd(), style=wx.FD_OPEN|wx.FD_CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not path in self._instrument.GetItems():
                self.select_instrument(path)
                            
        dlg.Destroy()        

    def select_instrument(self, path):

        s = subprocess.Popen([path,'-h'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        instrParams = dict([(v[0],[v[1],v[2]]) for v in re.findall("(\w+)\s*\((\w+)\)\s*\[default=\'(\S+)\'\]",s.communicate()[0])])
        self._instrument.Append(path)
        self._instrument.Select(self._instrument.GetCount()-1)
            
        pub.sendMessage("set_instrument", message = (self, instrParams))
        
    def on_select_instrument(self, event):
        
        if event.GetString() == self._instrument.GetStringSelection():
            return
        
        self.select_instrument(event.GetString())

    def get_widget_value(self):
        
        return self._instrument.GetStringSelection()

    def set_widget_value(self):
        
        pass
