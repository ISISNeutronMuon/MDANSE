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

import wx

from MDANSE.App.GUI.ConfiguratorWidgets.IConfiguratorWidget import ConfiguratorWidgetError, IConfiguratorWidget
    
class VectorConfigurator(IConfiguratorWidget):
    
    type = "vector"
    
    def initialize(self):
        pass

    def add_widgets(self):

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        gbSizer = wx.GridBagSizer(5,5)
        
        xLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="x-component")
        yLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="y-component")
        zLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="z-component")

        self._x = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
        self._y = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
        self._z = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
            
        cfg = self.configurator

        self._x.SetValue(str(cfg.default[0]))
        self._y.SetValue(str(cfg.default[1]))
        self._z.SetValue(str(cfg.default[2]))

        gbSizer.Add(xLabel, (0,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(yLabel, (0,3), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(zLabel,  (0,6), flag=wx.ALIGN_CENTER_VERTICAL)

        gbSizer.Add(self._x, (0,1), flag=wx.EXPAND)
        gbSizer.Add(self._y,  (0,4), flag=wx.EXPAND)
        gbSizer.Add(self._z,  (0,7), flag=wx.EXPAND)

        sizer.Add(gbSizer, 1, wx.ALL|wx.EXPAND, 5)

        return sizer      
    
    def get_widget_value(self):
        
        try:
            
            val = (self.configurator.valueType(self._x.GetValue()),
                   self.configurator.valueType(self._y.GetValue()),
                   self.configurator.valueType(self._z.GetValue()))
        except ValueError:
            raise ConfiguratorWidgetError("Invalid value for %r entry" % self.configurator.name)
        else:        
            return val

    def set_widget_value(self, value):
        pass