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

from MDANSE.Externals.pubsub import pub

from MDANSE.App.GUI import DATA_CONTROLLER
from MDANSE.App.GUI.Framework.Widgets.IWidget import IWidget

class InterpolationOrderWidget(IWidget):
    
    type = "interpolation_order"

    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="interpolation order")
        
        self._interpolationOrder = wx.Choice(self._widgetPanel, wx.ID_ANY)
                
        sizer.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self._interpolationOrder, 0, wx.ALL, 5)
                        
        pub.subscribe(self.on_set_trajectory, ("set_trajectory"))
        
        return sizer
                                                            
    def on_set_trajectory(self, message):                

        window, filename = message
                        
        if not window in self.Parent.widgets.values():
            return

        trajectory = DATA_CONTROLLER[filename]
                
        if "velocities" in trajectory.data.variables():
            self._interpolationOrder.SetItems(self._configurator.choices)
        else:
            self._interpolationOrder.SetItems(self._configurator.choices[1:])
            
        self._interpolationOrder.SetStringSelection(self._configurator.choices[0])
                    
    def get_widget_value(self):
             
        value = self._interpolationOrder.GetStringSelection()
        
        return value
