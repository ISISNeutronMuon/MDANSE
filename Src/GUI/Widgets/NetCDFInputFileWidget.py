# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/NetCDFInputFileWidget.py
# @brief     Implements module/class/test NetCDFInputFileWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

import netCDF4

from MDANSE import REGISTRY
from MDANSE.Framework.Configurable import ConfigurationError

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Widgets.IWidget import IWidget
    
class NetCDFInputFileWidget(IWidget):
        
    def __getattr__(self, attr):
        
        return self._netcdf.variables[attr][:]

    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._selectNetCDF = wx.Choice(self._widgetPanel, wx.ID_ANY)

        sizer.Add(self._selectNetCDF, 1, wx.ALL|wx.EXPAND, 5)
        
        self.Bind(wx.EVT_CHOICE, self.on_select_netcdf, self._selectNetCDF)
                
        return sizer

    def on_select_netcdf(self, event):
        
        filename = event.GetString()
                
        PUBLISHER.sendMessage("msg_set_netcdf", message=(self,filename))

    def set_data(self, datakey):
                        
        self._netcdf = DATA_CONTROLLER[datakey].netcdf
                        
        if not isinstance(self._netcdf, netCDF4.Dataset):
            return

        self._selectNetCDF.SetItems(list(DATA_CONTROLLER.keys()))
        
        self._selectNetCDF.SetStringSelection(datakey)
        
        PUBLISHER.sendMessage("msg_set_netcdf", message=(self,datakey))
                
    def get_widget_value(self):
        
        filename = self._selectNetCDF.GetStringSelection()
        
        if not filename:
            raise ConfigurationError("No NetCDF file selected", self)
        
        return filename
    
REGISTRY["netcdf_input_file"] = NetCDFInputFileWidget
