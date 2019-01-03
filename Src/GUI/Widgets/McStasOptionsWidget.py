# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/McStasOptionsWidget.py
# @brief     Implements module/class/test McStasOptionsWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import wx

from MDANSE import REGISTRY
from MDANSE.Framework.Configurable import Configurable
from MDANSE.GUI.ComboWidgets.ConfigurationPanel import ConfigurationPanel
from MDANSE.GUI.Widgets.IWidget import IWidget

class McStasOptionsWidget(IWidget):
     
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
    
REGISTRY["mcstas_options"] = McStasOptionsWidget
