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
Created on May 28, 2015

@author: Eric C. Pellegrini
'''

import collections

import wx
import wx.aui as wxaui
import wx.lib.filebrowsebutton as wxfile

from MDANSE import LOGGER, PREFERENCES
from MDANSE.Core.Error import Error
from MDANSE.Core.Preferences import PreferencesError

class PreferencesSettingsDialogError(Error):
    pass

class PreferencesItemWidget(wx.Panel):
    
    def __init__(self, parent, name, item, *args, **kwargs):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kwargs)

        self._parent = parent
        
        self._name = name
        
        self._item = item

        self.build_panel()
        
class InputDirectoryWidget(PreferencesItemWidget):
    
    type = "input_directory"

    def build_panel(self):

        sb = wx.StaticBox(self, wx.ID_ANY, label=self._item.name)
        
        self._widget = wxfile.DirBrowseButton(self, wx.ID_ANY, startDirectory=self._item.value)
        self._widget.SetValue(self._item.value)

        sizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        
        sizer.Add(self._widget, 1, wx.ALL|wx.EXPAND, 5)
                
        self.SetSizer(sizer)
    
    def get_value(self):
        
        return self._widget.GetValue()


    def set_value(self, value):
        
        self._widget.SetValue(value)

class LoggingLevelWidget(PreferencesItemWidget):
    
    type = "logging_level"

    def build_panel(self):

        sb = wx.StaticBox(self, wx.ID_ANY, label=self._item.name)

        self._widget = wx.Choice(self, wx.ID_ANY, choices=LOGGER.levels.keys())
        self._widget.SetStringSelection(PREFERENCES[self._item.name])

        sizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)

        sizer.Add(self._widget, 1, wx.ALL|wx.EXPAND, 5)
                
        self.SetSizer(sizer)

    def get_value(self):
        
        return self._widget.GetStringSelection()

    def set_value(self, value):
        
        return self._widget.SetStringSelection(value)
                        
WIDGETS = dict([(v.type,v) for v in PreferencesItemWidget.__subclasses__()])    

class PreferencesSettingsDialog(wx.Dialog):
    
    def __init__(self, parent=None):
        
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Preferences settings", size=(400,400), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)

        self._parent = parent

        self.build_dialog()

    def build_dialog(self):
                
        self._notebook = wxaui.AuiNotebook(self, wx.ID_ANY)
                
        self._sectionPanels = collections.OrderedDict()
        self._sectionSizers = collections.OrderedDict()
        self._widgets = collections.OrderedDict()
                
        for item in PREFERENCES.items.values():
            section = item.section
            name = item.name
            typ = item.type
            if not self._sectionPanels.has_key(section):
                self._sectionPanels[section] = wx.ScrolledWindow(self, wx.ID_ANY)
                self._sectionPanels[section].SetScrollbars(1,1,200,200)
                self._sectionSizers[section] = wx.BoxSizer(wx.VERTICAL)
                
            self._widgets[name] = WIDGETS[typ](self._sectionPanels[section], name, item)
            self._sectionSizers[section].Add(self._widgets[name], 0, wx.ALL|wx.EXPAND, 5)
                                
        for k,v in self._sectionPanels.items():
            v.SetSizer(self._sectionSizers[k])
            self._notebook.AddPage(v, k)
                    
        sb = wx.StaticBox(self, wx.ID_ANY)
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        
        cancelButton = wx.Button(self, wx.ID_ANY, label="Cancel")
        defaultButton = wx.Button(self, wx.ID_ANY, label="Default")
        okButton = wx.Button(self, wx.ID_ANY, label="OK")
        
        sbSizer.Add(cancelButton, 0, wx.ALL, 5)
        sbSizer.Add((-1,-1), 1, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add(defaultButton, 0, wx.ALL, 5)
        sbSizer.Add(okButton, 0, wx.ALL, 5)
                    
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._sizer.Add(self._notebook, 1, wx.ALL|wx.EXPAND, 5)

        self._sizer.Add(sbSizer, 0, wx.ALL|wx.EXPAND, 5)
            
        self.SetSizer(self._sizer)
            
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancelButton)
        self.Bind(wx.EVT_BUTTON, self.on_default, defaultButton)
        self.Bind(wx.EVT_BUTTON, self.on_ok, okButton)
        
    def on_cancel(self, event):
        
        self.Close()
        
    def on_default(self, event):
        
        for v in PREFERENCES.values():
            self._widgets[v.name].set_value(v.default)

    def on_ok(self, event):
        
        if not self.validate():
            return
        
        d = wx.MessageDialog(None, 'Save the preferences ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:

            try:
                PREFERENCES.save()
                
            except PreferencesError as e:
                d = wx.MessageDialog(self, str(e), style=wx.ICON_ERROR|wx.STAY_ON_TOP|wx.CENTRE)
                d.ShowModal()
                return
                                    
        self.Close()
            
    def validate(self):

        for w in self._widgets.values():
            w.SetBackgroundColour(wx.NullColour)
            w.Refresh()

        for k, v in self._widgets.items():

            try:
                PREFERENCES[k] = v.get_value()
            except PreferencesError as e:
                d = wx.MessageDialog(self, str(e), style=wx.ICON_ERROR|wx.STAY_ON_TOP|wx.CENTRE)
                d.ShowModal()
                v.SetBackgroundColour("Pink")
                v.Refresh()
                v.SetFocus()
                return False

        return True                    
        
if __name__ == "__main__":
    
    app = wx.App(False)
    
    d = PreferencesSettingsDialog(None)
    
    d.ShowModal()
    
    app.MainLoop()
    
