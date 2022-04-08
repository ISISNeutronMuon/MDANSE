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

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.ComboWidgets.ComboCheckbox import ComboCheckbox
from MDANSE.GUI.Widgets.IWidget import IWidget

def get_unique_filename(directory,basename):

    filesInDirectory = [os.path.join(directory,e) for e in os.listdir(directory) 
                        if os.path.isfile(os.path.join(directory,e))]
    basenames = [os.path.splitext(f)[0] for f in filesInDirectory]

    initialPath = path = os.path.join(directory,basename)
    comp = 1
    while True:
        if path in basenames:
            path = '%s(%d)' % (initialPath,comp)
            comp += 1
            continue
        return path

class OutputFilesWidget(IWidget):

    def __init__(self, *args, **kwargs):

        IWidget.__init__(self, *args, **kwargs)

        PUBLISHER.subscribe(self.msg_input_file_set, 'input_file_loaded')

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
    
    def msg_input_file_set(self, message):

        configurator, filename = message

        if self._configurator.root is None:
            return

        if self._configurator.root == configurator.name:
            filenameWithoutExt = os.path.splitext(filename)[0]
            outputFileWithoutExt = '%s_converted' % filenameWithoutExt
            directory,basename = os.path.split(outputFileWithoutExt)
            path = get_unique_filename(directory,basename)
            self._filename.SetValue(path)

    def set_data(self, datakey, analysis):
                
        if datakey is None:
            basename = "output_%s" % analysis
            trajectoryDir = os.getcwd()
        else:
            basename = "%s_%s" % (os.path.splitext(os.path.basename(datakey))[0], analysis)
            trajectoryDir = os.path.dirname(datakey)

        path = get_unique_filename(trajectoryDir,basename)

        self._filename.SetValue(path)
        
REGISTRY["output_files"] = OutputFilesWidget
