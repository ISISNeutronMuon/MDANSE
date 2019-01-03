import os
import re
import subprocess

import wx

from MDANSE import REGISTRY

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.Widgets.IWidget import IWidget

class McStasInstrumentWidget(IWidget):
    
    _mcStasTypes = {'double' : float, 'int' : int, 'string' : str}

    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._instrument = wx.Choice(self._widgetPanel, wx.ID_ANY)
        
        self._browse = wx.Button(self._widgetPanel, wx.ID_ANY, label="Browse")

        sizer.Add(self._instrument, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self._browse, 0, wx.ALL, 5)
        
        self.Bind(wx.EVT_CHOICE, self.on_select_instrument, self._instrument)
        self.Bind(wx.EVT_BUTTON, self.on_browse_instrument, self._browse)
        
        return sizer

    def on_browse_instrument(self, event):
        
        dlg = wx.FileDialog(self, "select instrument executable", os.getcwd(), style=wx.FD_OPEN|wx.FD_CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not path in self._instrument.GetItems():
                self.select_instrument(path)
                            
        dlg.Destroy()        

    def select_instrument(self, path):

        s = subprocess.Popen([path,'-h'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        instrParams = dict([(v[0],[v[1],v[2]]) for v in re.findall("(\w+)\s*\((\w+)\)\s*\[default=\'(\S+)\'\]",s.communicate()[0])])
        self._instrument.Append(path)
        self._instrument.Select(self._instrument.GetCount()-1)
            
        PUBLISHER.sendMessage("msg_set_instrument", message=(self, instrParams))
        
    def on_select_instrument(self, event):
        
        if event.GetString() == self._instrument.GetStringSelection():
            return
        
        self.select_instrument(event.GetString())

    def get_widget_value(self):
        
        return self._instrument.GetStringSelection()
    
REGISTRY["mcstas_instrument"] = McStasInstrumentWidget
