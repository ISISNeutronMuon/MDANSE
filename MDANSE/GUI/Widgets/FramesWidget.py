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
import wx.lib.intctrl as wxintctrl

from MDANSE import REGISTRY
from MDANSE.Framework.InputData.EmptyData import EmptyData

from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Widgets.IWidget import IWidget
        
class FramesWidget(IWidget):
            
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        gbSizer = wx.GridBagSizer(5,5)
        
        firstLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="First frame")
        self._first = wxintctrl.IntCtrl(self._widgetPanel, wx.ID_ANY, limited=True, allow_none=False)

        labelLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="Last frame")
        self._last = wxintctrl.IntCtrl(self._widgetPanel, wx.ID_ANY, limited=True, allow_none=False)

        stepLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="Frame step")
        self._step = wxintctrl.IntCtrl(self._widgetPanel, wx.ID_ANY, limited=True, allow_none=False)

        gbSizer.Add(firstLabel, (0,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(labelLabel, (0,3), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(stepLabel,  (0,6), flag=wx.ALIGN_CENTER_VERTICAL)

        gbSizer.Add(self._first, (0,1), flag=wx.EXPAND)
        gbSizer.Add(self._last,  (0,4), flag=wx.EXPAND)
        gbSizer.Add(self._step,  (0,7), flag=wx.EXPAND)

        gbSizer.AddGrowableCol(1)
        gbSizer.AddGrowableCol(4)
        gbSizer.AddGrowableCol(7)

        sizer.Add(gbSizer, 1, wx.ALL|wx.EXPAND, 5)

        return sizer

    def get_widget_value(self):
        
        val = (self._first.GetValue(), self._last.GetValue(), self._step.GetValue())
        
        return val
    
    def set_data(self, datakey):
        
        self._trajectory = DATA_CONTROLLER[datakey]
                
        nFrames = len(self._trajectory.data) - 1
                
        self._first.SetMin(0)
        self._first.SetMax(nFrames-1)
        self._first.SetValue(0)

        self._last.SetMin(1)
        self._last.SetMax(nFrames)
        self._last.SetValue(nFrames)

        self._step.SetMin(1)
        self._step.SetMax(nFrames)
        self._step.SetValue(1)
        
    @property
    def time(self):
        
        f, l, s = self.get_value()
        
        time = self._trajectory.data.time[f:l:s]
        
        return time

REGISTRY["frames"] = FramesWidget
