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

import os

import wx.combo
import wx.lib.filebrowsebutton as wxfile

from MDANSE.Externals.pubsub import pub

from MDANSE.App.GUI.ComboWidgets.ComboCheckbox import ComboCheckbox
from MDANSE.App.GUI.Framework.Plugins.IPlugin import plugin_parent
from MDANSE.App.GUI.Framework.Widgets.IWidget import IWidget

class OutputFilesWidget(IWidget):
    
    type = "output_files"

    def initialize(self):
        
        self._availableFormats = self.configurator.formats
                
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)
                
        startDirectory = os.getcwd()
        
        self._dirname = wxfile.DirBrowseButton(self._widgetPanel, wx.ID_ANY, startDirectory=startDirectory, newDirectory=True)
        self._dirname.SetValue(startDirectory)

        label = wx.StaticText(self._widgetPanel, label="Basename", style=wx.ALIGN_LEFT)
        
        self._basename = wx.TextCtrl(self._widgetPanel, value="")

        self._formats = wx.combo.ComboCtrl(self._widgetPanel, value="output formats", style=wx.CB_READONLY)
        
        tcp = ComboCheckbox(self._availableFormats)

        self._formats.SetPopupControl(tcp)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        hSizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        hSizer.Add(self._basename, 1, wx.EXPAND|wx.ALL, 5)
        hSizer.Add(self._formats, 0, wx.ALL, 5)

        sizer.Add(self._dirname, 0, wx.ALL|wx.EXPAND)
        sizer.Add(hSizer, 0, wx.ALL|wx.EXPAND, 0)

        pub.subscribe(self.set_widget_value, ("set_trajectory"))
        
        return sizer

    def get_widget_value(self):
        
        dirname = self._dirname.GetValue()
        
        basename = self._basename.GetValue().strip()
                
        formats = self._formats.GetPopupControl().GetControl().GetCheckedStrings()
                                    
        return (dirname, basename, formats)
    
    
    def set_widget_value(self, message):
        
        window, filename = message
                        
        if not window in self.Parent.widgets.values():
            return
                
        self._basename.SetValue("output_%s" % (os.path.splitext(os.path.basename(filename))[0]))