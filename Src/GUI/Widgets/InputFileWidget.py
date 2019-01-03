# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/InputFileWidget.py
# @brief     Implements module/class/test InputFileWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx
import wx.lib.filebrowsebutton as wxfile

from MDANSE import REGISTRY
from MDANSE.Framework.Configurable import ConfigurationError
from MDANSE.GUI.Widgets.IWidget import IWidget

class InputFileWidget(IWidget):
        
    def add_widgets(self):
        
        default = self._configurator.default
        wildcard = self._configurator.wildcard

        sizer = wx.BoxSizer(wx.VERTICAL)
                
        self._browser = wxfile.FileBrowseButton(self._widgetPanel, wx.ID_ANY, labelText="", initialValue=default, startDirectory=default,fileMask=wildcard)

        sizer.Add(self._browser, 1, wx.ALL|wx.EXPAND, 5)

        return sizer
        
    def get_widget_value(self):

        filename = self._browser.GetValue()

        if not filename:
            raise ConfigurationError("No input file selected", self)

        return filename
    
REGISTRY["input_file"] = InputFileWidget
