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

import os

import wx.combo
import wx.lib.filebrowsebutton as wxfile

from MDANSE.Externals.pubsub import pub

from MDANSE.App.GUI.ComboWidgets.ComboCheckbox import ComboCheckbox
from MDANSE.App.GUI.Framework.Widgets.IWidget import IWidget

class OutputFilesWidget(IWidget):
    
    type = "output_files"
        
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)
                        
        self._filename = wxfile.FileBrowseButton(self._widgetPanel, wx.ID_ANY, fileMode=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT, labelText="Basename")
        
        self._formats = wx.combo.ComboCtrl(self._widgetPanel, value="output formats", style=wx.CB_READONLY)
        
        tcp = ComboCheckbox(self._configurator.formats)

        self._formats.SetPopupControl(tcp)
        
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        hSizer.Add(self._filename, 1, wx.EXPAND|wx.ALL, 5)
        hSizer.Add(self._formats, 0, wx.EXPAND|wx.ALL, 5)

        sizer.Add(hSizer, 0, wx.ALL|wx.EXPAND, 0)

        pub.subscribe(self.on_set_trajectory, ("set_trajectory"))
        
        return sizer

    def get_widget_value(self):
        
        filename = self._filename.GetValue()
                        
        formats = self._formats.GetPopupControl().GetControl().GetCheckedStrings()
                                    
        return (filename, formats)
    
    def on_set_trajectory(self, message):
        
        window, filename = message
                        
        if not window in self.Parent.widgets.values():
            return
        
        trajectoryDir = os.path.dirname(filename)
        basename = "output_%s" % os.path.splitext(os.path.basename(filename))[0]
        
        self._filename.SetValue(os.path.join(trajectoryDir,basename))
                        
