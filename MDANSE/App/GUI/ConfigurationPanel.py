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
Created on Apr 10, 2015

@author: pellegrini
'''

import wx

from MDANSE import REGISTRY
from MDANSE.Framework.Configurable import ConfigurationError

class ConfigurationPanel(wx.Panel):
    
    def __init__(self, parent, configuration):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self._configuration = configuration
        
        self._widgets = {}
        
        self.build_panel()
        
    def build_panel(self):
        
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)

        for cfg in self._configuration.configurators.values():

            widgetClass = REGISTRY["configuratorwidget"][cfg.widget]
                        
            self._widgets[cfg.name] = widgetClass(self, cfg.name, self._configuration)
            
            self.panelSizer.Add(self._widgets[cfg.name], 0, wx.ALL|wx.EXPAND, 5)
                  
        self.SetSizer(self.panelSizer)
                                   
        self.Layout()

        self.Fit()
            
    @property
    def widgets(self):
        return self._widgets
            
    def get_value(self):
        
        return dict([(k,v.get_value()) for k,v in self._widgets.items()])
    
    def validate(self):

        for w in self._widgets.values():
            w.SetBackgroundColour(wx.NullColour)
            w.Refresh()
             
        try:
            self._configuration.setup(self.get_value())
        except ConfigurationError as e:
            d = wx.MessageDialog(self, str(e), style=wx.ICON_ERROR|wx.STAY_ON_TOP|wx.CENTRE)
            d.ShowModal()
            w = self._widgets[e.configurator.name]
            w.SetBackgroundColour("Pink")
            w.Refresh()
            w.SetFocus()
            return False
        else:
            return True
