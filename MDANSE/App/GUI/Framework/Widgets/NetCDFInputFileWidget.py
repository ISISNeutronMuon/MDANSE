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

from Scientific.IO.NetCDF import _NetCDFFile

from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.Configurable import ConfigurationError

from MDANSE.App.GUI import DATA_CONTROLLER
from MDANSE.App.GUI.Framework.Widgets.IWidget import IWidget
    
class NetCDFInputWidget(IWidget):
    
    type = "netcdf_input_file"
    
    def __getattr__(self, attr):
        
        return self._netcdf.variables[attr].getValue()

    def initialize(self):        
        pass

    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._selectNetCDF = wx.Choice(self._widgetPanel, wx.ID_ANY)

        sizer.Add(self._selectNetCDF, 1, wx.ALL|wx.EXPAND, 5)
        
        self.Bind(wx.EVT_CHOICE, self.on_select_netcdf, self._selectNetCDF)
        
        pub.subscribe(self.set_netcdf, ('on_set_data'))
        
        return sizer


    def on_select_netcdf(self, event):
        
        filename = event.GetString()
                
        pub.sendMessage("set_netcdf", message=(self,filename))

    
    def set_netcdf(self, message):
        
        window, filename = message
                
        if not self.has_parent(window):
            return
                
        self._netcdf = DATA_CONTROLLER[filename].netcdf
                        
        if not isinstance(self._netcdf, _NetCDFFile):
            return

        self._selectNetCDF.SetItems(DATA_CONTROLLER.keys())
        
        self._selectNetCDF.SetStringSelection(filename)
        
        pub.sendMessage("set_netcdf", message = (self,filename))
                
                
    def get_widget_value(self):
        
        filename = self._selectNetCDF.GetStringSelection()
        
        if not filename:
            raise ConfigurationError("No NetCDF file selected", self)
        
        return filename
    

    def set_widget_value(self, value):
        pass
