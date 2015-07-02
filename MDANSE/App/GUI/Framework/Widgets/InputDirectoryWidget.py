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
import wx.lib.filebrowsebutton as wxfile

from MDANSE.App.GUI.Framework.Widgets.IWidget import IWidget

class InputDirectoryWidget(IWidget):
    
    type = "input_directory"
    
    def add_widgets(self):
        
        cfg = self.configurator

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._dirname = wxfile.DirBrowseButton(self._widgetPanel, wx.ID_ANY, startDirectory=cfg.default, newDirectory=True)
        self._dirname.SetValue(cfg.default)

        sizer.Add(self._dirname, 1, wx.ALL|wx.EXPAND, 0)
        
        return sizer

    def get_widget_value(self):
        
        dirname = self._dirname.GetValue()
                                            
        return dirname