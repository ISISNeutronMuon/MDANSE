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

import collections

import wx

from MDANSE.GUI.ComboWidgets.ConfigurationPanel import ConfigurationPanel
from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.Widgets.IWidget import IWidget

class McStasOptionsConfiguratorWidget(IWidget):
     
    type = "mcstas_options"

    _mcStasTypes = {'double' : 'float', 'int' : 'integer', 'str' : 'input_file'}
 
    def add_widgets(self):
         
        sizer = wx.BoxSizer(wx.VERTICAL)
  
        options = Configurable()
        
        settings = collections.OrderedDict()
        for name,value in self._configurator.default.items():
            settings[name] = (self._mcStasTypes[type(value).__name__],{'default':value})
        
        options.set_settings(settings)                    
         
        self._panel = ConfigurationPanel(self._widgetPanel, options)
         
        sizer.Add(self._panel, 0, wx.ALL|wx.EXPAND, 5)
         
        return sizer
         
    def get_widget_value(self):
         
        val = self._panel.get_value()
         
        return val