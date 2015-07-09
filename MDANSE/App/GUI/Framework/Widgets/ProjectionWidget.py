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

class ProjectionWidget(IWidget):
    
    type = "projection"

    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        gbSizer = wx.GridBagSizer(0,0)

        self._none = wx.RadioButton(self._widgetPanel, wx.ID_ANY, label="None", style=wx.RB_GROUP)
        self._none.SetValue(True)
        self._axial = wx.RadioButton(self._widgetPanel, wx.ID_ANY, label="Axial")
        self._planar = wx.RadioButton(self._widgetPanel, wx.ID_ANY, label="Planar")

        self._panelAxial = wx.Panel(self._widgetPanel, wx.ID_ANY)
        sizerAxial = wx.BoxSizer(wx.HORIZONTAL)
        
        labelAxial = wx.StaticText(self._panelAxial, wx.ID_ANY, size=(80,-1), label="Axis vector")        
        self._ax = wx.TextCtrl(self._panelAxial, wx.ID_ANY)
        self._ay = wx.TextCtrl(self._panelAxial, wx.ID_ANY)
        self._az = wx.TextCtrl(self._panelAxial, wx.ID_ANY)

        sizerAxial.Add(labelAxial, flag=wx.ALIGN_CENTER_VERTICAL)
        sizerAxial.Add(self._ax, 1, wx.EXPAND|wx.ALL, 5)
        sizerAxial.Add(self._ay, 1, wx.EXPAND|wx.ALL, 5)
        sizerAxial.Add(self._az, 1, wx.EXPAND|wx.ALL, 5)

        self._panelAxial.SetSizer(sizerAxial)
        self._panelAxial.Enable(False)

        self._panelPlanar = wx.Panel(self._widgetPanel, wx.ID_ANY)
        sizerPlanar = wx.BoxSizer(wx.HORIZONTAL)

        labelPlanar = wx.StaticText(self._panelPlanar, wx.ID_ANY, size=(80,-1), label="Normal vector")        
        self._px = wx.TextCtrl(self._panelPlanar, wx.ID_ANY)
        self._py = wx.TextCtrl(self._panelPlanar, wx.ID_ANY)
        self._pz = wx.TextCtrl(self._panelPlanar, wx.ID_ANY)

        sizerPlanar.Add(labelPlanar, flag=wx.ALIGN_CENTER_VERTICAL)
        sizerPlanar.Add(self._px, 1, wx.EXPAND|wx.ALL, 5)
        sizerPlanar.Add(self._py, 1, wx.EXPAND|wx.ALL, 5)
        sizerPlanar.Add(self._pz, 1, wx.EXPAND|wx.ALL, 5)

        self._panelPlanar.SetSizer(sizerPlanar)
        self._panelPlanar.Enable(False)

        gbSizer.Add(self._none, (0,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self._axial, (1,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self._planar, (2,0), flag=wx.ALIGN_CENTER_VERTICAL)

        gbSizer.Add(self._panelAxial, (1,2), flag=wx.EXPAND)

        gbSizer.Add(self._panelPlanar, (2,2), flag=wx.EXPAND)

        sizer.Add(gbSizer, 1, wx.EXPAND|wx.ALL, 5)
        
        self.Bind(wx.EVT_RADIOBUTTON, self.on_select_projection_mode, self._none)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_select_projection_mode, self._axial)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_select_projection_mode, self._planar)
        
        return sizer

    def get_widget_value(self):

        rb = [rb for rb in (self._none, self._axial, self._planar) if rb.GetValue()][0]
        
        if rb == self._none:
            return None
        
        elif rb == self._axial:
            try:
                val = ("axial", tuple([float(v.GetValue()) for v in (self._ax,self._ay,self._az)]))
            except ValueError:
                raise ConfigurationError("Invalid value for %r entry" % self.name)
            else:
                return val
            
        elif rb == self._planar:
            try:
                val = ("planar", tuple([v.GetValue() for v in (self._px,self._py,self._pz)]))
            except ValueError:
                raise ConfigurationError("Invalid value for %r entry" % self.name)
            else:
                return val            
    
    def on_select_projection_mode(self, event):
        
        rb = event.GetEventObject()
        
        self._panelAxial.Enable(rb == self._axial)
        self._panelPlanar.Enable(rb == self._planar)
