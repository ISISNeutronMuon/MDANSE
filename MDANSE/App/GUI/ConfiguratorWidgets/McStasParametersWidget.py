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
 
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.Jobs.McStasVirtualInstrument import McStasParameters

from MDANSE.App.GUI.ConfiguratorWidgets.IConfiguratorWidget import ConfiguratorWidgetError,IConfiguratorWidget
from MDANSE.App.GUI.ConfigurationPanel import ConfigurationPanel

class McStasParametersWidget(IConfiguratorWidget):
 
    type = "mcstas_parameters"
     
    _mcStasTypes = {'double' : 'float', 'int' : 'integer', 'string' : 'input_file'}
 
    def initialize(self):
 
        self._configurationPanel = None
 
    def add_widgets(self):
         
        self._sizer = wx.BoxSizer(wx.VERTICAL)
 
        pub.subscribe(self.set_layout, ("set_instrument"))
         
        return self._sizer
  
    def set_layout(self, message):
 
        window, parameters = message
                             
        if not window in self.Parent.widgets.values():
            return
 
        for k in self.configurator.exclude:
            parameters.pop(k)
        
        self._mcstasParameters = McStasParameters()
         
        for name, value in parameters.items():
            typ, default = value
            self._mcstasParameters.configurators[name] = (self._mcStasTypes[typ], {"default":default})
 
        self._sizer.Clear(deleteWindows=True)
 
        self._widgetPanel.Freeze()
        self._configurationPanel = ConfigurationPanel(self._widgetPanel, self._mcstasParameters)
         
        for name, value in parameters.items():
            typ, default = value
            if typ == 'string':
                self._configurationPanel.widgets[name]._browser.SetLabel('Text/File Entry')
                 
        self._sizer.Add(self._configurationPanel, 1, wx.ALL|wx.EXPAND, 5)
 
        self._widgetPanel.Thaw()
         
        self.Parent.Layout()
         
        # Trick to show the escrollbar after updating the configuration panel.
        self.Parent.Parent.SendSizeEvent()
         
 
    def get_widget_value(self):
        if self._configurationPanel is None:
            raise ConfiguratorWidgetError('McStas instrument is not yet defined')
         
        val = self._configurationPanel.get_value()
         
        return val 
 
         
    def set_widget_value(self):
        pass