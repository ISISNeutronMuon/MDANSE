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

from MDANSE.Mathematics.Signal import INTERPOLATION_ORDER

from MDANSE.App.GUI import DATA_CONTROLLER
from MDANSE.App.GUI.ConfiguratorWidgets.IConfiguratorWidget import IConfiguratorWidget

class InterpolationOrderWidget(IConfiguratorWidget):
    
    type = "interpolation_order"

    def initialize(self):
        pass


    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="interpolation order")
        
        self._interpolationOrder = wx.SpinCtrl(self._widgetPanel, min=-1, max=len(INTERPOLATION_ORDER)-1, initial=0, style=wx.SP_WRAP|wx.SP_ARROW_KEYS)

        self._info = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="")
                
        sizer.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self._interpolationOrder, 0, wx.ALL, 5)
        sizer.Add(self._info, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
                
        self._interpolationOrder.Bind(wx.EVT_SPIN, self.on_select_interpolation_order)
        
        pub.subscribe(self.set_wigdet_value, ("set_trajectory"))
        
        self.select_interpolation_order(-1)

        return sizer
                
    def select_interpolation_order(self, order):
        
        self._interpolationOrder.SetValue(order)
                
        if order == -1:
            self._info.SetLabel("The velocities will be taken directly from the trajectory.")
        else:
            self._info.SetLabel("The velocities will be derived from coordinates using order-%d interpolation." % order)
                                
    def on_select_interpolation_order(self, event):

        order = event.GetPosition()
        
        self.select_interpolation_order(order)
        
    def set_wigdet_value(self, message):                

        window, filename = message
                        
        if not window in self.Parent.widgets.values():
            return

        trajectory = DATA_CONTROLLER[filename]
                
        if "velocities" in trajectory.data.variables():
            order = -1
        else:
            order = 0

        self._interpolationOrder.SetRange(order,len(INTERPOLATION_ORDER)-1)
        
        self.select_interpolation_order(order)    
            

    def get_widget_value(self):        
        value = self._interpolationOrder.GetValue()
        
        return value

    def set_widget_value(self, value):
        pass
