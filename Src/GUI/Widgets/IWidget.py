# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/IWidget.py
# @brief     Implements module/class/test IWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc
        
import wx

from MDANSE.GUI import PUBLISHER

class IWidget(wx.Panel):
        
    _registry = "widget"

    def __init__(self, parent, name, configurator, *args, **kwargs):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kwargs)

        self._parent = parent
        
        self._name = name
                                
        self._configurator = configurator
                                                        
        self._label = self._configurator.label
                        
        self.initialize()
                        
        self.build_panel()
        
        self.Bind(wx.EVT_WINDOW_DESTROY,self.OnDestroy)
        
        PUBLISHER.subscribe(self._set_data, 'msg_set_data')
                        
    @property
    def label(self):
        return self._label

    @property
    def name(self):
        return self._name

    def initialize(self):
        pass

    @abc.abstractmethod
    def get_widget_value(self):
        pass
                
    @abc.abstractmethod
    def add_widgets(self):
        pass
    
    def build_panel(self):        

        self._staticBox = wx.StaticBox(self, wx.ID_ANY, label=self.label)

        self._staticBoxSizer = wx.StaticBoxSizer(self._staticBox, wx.VERTICAL)
                
        self._widgetPanel = wx.Panel(self, wx.ID_ANY)

        self._widgetPanelSizer = self.add_widgets()
        
        self._widgetPanel.SetSizer(self._widgetPanelSizer)
        
        self._staticBoxSizer.Add(self._widgetPanel, 1, wx.ALL|wx.EXPAND, 0)
        
        self.SetSizer(self._staticBoxSizer)
        
        self._widgetPanel.GrandParent.Refresh()
                
    def get_value(self):
        
        return self.get_widget_value()

    def set_data(self,datakey):
        pass

    def _set_data(self,message):
                
        plugin = message
        if not plugin.is_parent(self):
            return
        
        self.set_data(plugin.datakey)

    def OnDestroy(self,event):
                
        PUBLISHER.unsubscribe(self._set_data, 'msg_set_data')
        event.Skip()
