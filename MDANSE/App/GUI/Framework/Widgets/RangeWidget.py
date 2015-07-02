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

import wx

from MDANSE.Framework.Configurable import ConfigurationError

from MDANSE.App.GUI.Framework.Widgets.IWidget import IWidget

class RangeWidget(IWidget):

    type = "range"

    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        gbSizer = wx.GridBagSizer(5,5)
        
        firstLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="from")
        labelLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="to")
        stepLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="by step of")

        self._first = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
        self._last  = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
        self._step  = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
                    
        cfg = self.configurator
        
        self._first.SetValue(str(cfg.default[0]))
        self._last.SetValue(str(cfg.default[1]))
        self._step.SetValue(str(cfg.default[2]))

        gbSizer.Add(firstLabel, (0,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(labelLabel, (0,3), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(stepLabel,  (0,6), flag=wx.ALIGN_CENTER_VERTICAL)

        gbSizer.Add(self._first, (0,1), flag=wx.EXPAND)
        gbSizer.Add(self._last,  (0,4), flag=wx.EXPAND)
        gbSizer.Add(self._step,  (0,7), flag=wx.EXPAND)

        sizer.Add(gbSizer, 1, wx.ALL|wx.EXPAND, 5)

        return sizer
        
    def get_widget_value(self):
        
        try:
            val = (self.configurator.valueType(self._first.GetValue()),
                   self.configurator.valueType(self._last.GetValue()),
                   self.configurator.valueType(self._step.GetValue()))
        except ValueError:
            raise ConfigurationError("Invalid value for %r entry" % self.configurator.name)
        else:
            return val
