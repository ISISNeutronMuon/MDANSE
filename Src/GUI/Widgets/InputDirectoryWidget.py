# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/InputDirectoryWidget.py
# @brief     Implements module/class/test InputDirectoryWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx
import wx.lib.filebrowsebutton as wxfile

from MDANSE import REGISTRY
from MDANSE.GUI.Widgets.IWidget import IWidget

class InputDirectoryWidget(IWidget):
        
    def add_widgets(self):
        
        default = self._configurator.default

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._dirname = wxfile.DirBrowseButton(self._widgetPanel, wx.ID_ANY, startDirectory=default, newDirectory=True)
        self._dirname.SetValue(default)

        sizer.Add(self._dirname, 1, wx.ALL|wx.EXPAND, 0)
        
        return sizer

    def get_widget_value(self):
        
        dirname = self._dirname.GetValue()
                                            
        return dirname
    
REGISTRY["input_directory"] = InputDirectoryWidget
