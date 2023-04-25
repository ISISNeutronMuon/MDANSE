# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/ComboWidgets/ConfigurationPanel.py
# @brief     Implements module/class/test ConfigurationPanel
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

from MDANSE import REGISTRY

from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError

class ConfigurationPanel(wx.Panel):
    
    def __init__(self, parent, configurable, type):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self._configurable = configurable
        
        self._type = type
        
        self._widgets = {}
        
        self.build_panel()
        
    def build_panel(self):
        
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)

        self._configurable.build_configuration()

        for cfgName in self._configurable.settings.keys():
            
            widget = self._configurable.configuration[cfgName].widget
                        
            widgetClass = REGISTRY["widget"][widget]
                        
            self._widgets[cfgName] = widgetClass(self, cfgName, self._configurable.configuration[cfgName], widget)
            
            self.panelSizer.Add(self._widgets[cfgName], 0, wx.ALL|wx.EXPAND, 5)
                  
        self.SetSizer(self.panelSizer)
                                   
        self.Layout()

        self.Fit()
                    
    @property
    def type(self):
        return self._type

    @property
    def widgets(self):
        return self._widgets
                 
    def get_value(self):
        
        return dict([(k,v.get_value()) for k,v in self._widgets.items()])
    
    def validate(self):
               
        parameters = {}
        try:
            parameters.update(self.get_value())
        except ConfiguratorError as e:
            wx.MessageBox(self, str(e), "Invalid input", style=wx.ICON_ERROR|wx.OK)
            return False
        finally:
            return True
