# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/OutputFilesWidget.py
# @brief     Implements module/class/test OutputFilesWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os
import os.path

import wx.combo
import wx.lib.filebrowsebutton as wxfile

from MDANSE import REGISTRY

from MDANSE.GUI.ComboWidgets.ComboCheckbox import ComboCheckbox
from MDANSE.GUI.Widgets.IWidget import IWidget

class OutputFilesWidget(IWidget):
            
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

        if len(self._configurator.formats) == 1:
            self._formats.Hide()

        return sizer

    def get_widget_value(self):
        
        filename = self._filename.GetValue()
                        
        formats = self._formats.GetPopupControl().GetControl().GetCheckedStrings()
                                    
        return (filename, formats)
    
    def set_data(self, datakey, analysis):
                
        if datakey is None:
            basename = "output_%s" % analysis
            trajectoryDir = os.getcwd()
        else:
            basename = "%s_%s" % (os.path.splitext(os.path.basename(datakey))[0], analysis)
            trajectoryDir = os.path.dirname(datakey)        

        filesInDirectory = [os.path.join(trajectoryDir,e) for e in os.listdir(trajectoryDir) 
                            if os.path.isfile(os.path.join(trajectoryDir,e))]
        basenames = [os.path.splitext(f)[0] for f in filesInDirectory]

        initialPath = path = os.path.join(trajectoryDir,basename)
        comp = 1
        while True:
            if path in basenames:
                path = '%s(%d)' % (initialPath,comp)
                comp += 1
                continue
            break           

        self._filename.SetValue(path)
        
REGISTRY["output_files"] = OutputFilesWidget
