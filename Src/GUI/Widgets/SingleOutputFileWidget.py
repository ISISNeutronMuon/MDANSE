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
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import glob
import itertools
import os
import os.path

import wx.combo
import wx.lib.filebrowsebutton as wxfile

from MDANSE import REGISTRY

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.ComboWidgets.ComboCheckbox import ComboCheckbox
from MDANSE.GUI.Widgets.IWidget import IWidget

class SingleOutputFileWidget(IWidget):

    def __init__(self, *args, **kwargs):

        IWidget.__init__(self, *args, **kwargs)

        PUBLISHER.subscribe(self.msg_input_file_set, 'input_file_loaded')

    @staticmethod
    def _get_unique_filename(filename):

        directory = os.path.dirname(filename)

        filesInDirectory = [os.path.join(directory,e) for e in itertools.chain(glob.iglob(os.path.join(directory,"*")),glob.iglob(os.path.join(directory,".*"))) 
                            if os.path.isfile(os.path.join(directory,e))]


        path = filename
        comp = 1
        while True:
            if path in filesInDirectory:
                filenameWithoutExtension = os.path.splitext(filename)[0]
                path = '%s(%d)' % (filenameWithoutExtension,comp)
                comp += 1
                continue
            return path

    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)
                        
        self._filename = wxfile.FileBrowseButton(self._widgetPanel, wx.ID_ANY, fileMode=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT, labelText="Filename")
                
        hSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        hSizer.Add(self._filename, 4, wx.EXPAND|wx.ALL, 5)

        sizer.Add(hSizer, 0, wx.ALL|wx.EXPAND, 0)

        return sizer

    def get_widget_value(self):
        
        filename = self._filename.GetValue()
                                                            
        return (os.path.splitext(filename)[0],self._configurator.format)
    
    def msg_input_file_set(self, message):

        configurator, inputFilename = message

        if self._configurator.root is None:
            return

        if self._configurator.root == configurator.name:
            inputFileNameWithoutExtension = os.path.splitext(inputFilename)[0]
            filename = '%s%s' % (inputFileNameWithoutExtension,REGISTRY['format'][self._configurator.format].extension)
            
            path = SingleOutputFileWidget._get_unique_filename(filename)
            self._filename.SetValue(path)

    def set_data(self, datakey):
        
        if datakey is None:
            filename = os.path.join(os.getcwd(),'output.nc')
        else:
            filename = datakey

        path = SingleOutputFileWidget._get_unique_filename(filename)

        self._filename.SetValue(path)
        
REGISTRY["single_output_file"] = SingleOutputFileWidget
