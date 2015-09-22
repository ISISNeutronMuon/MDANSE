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

:author: Eric C. Pellegrini
'''

import abc
import collections

import wx
import wx.aui as wxaui
import wx.lib.filebrowsebutton as wxfile

from MDANSE import PLATFORM, PREFERENCES

class WritableDirectoryValidator(wx.PyValidator):  

    def Clone(self):
        
        return WritableDirectoryValidator()
        

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True

class PreferencesItemWidget(wx.Panel):
    
    __metaclass__ = abc.ABCMeta 
    
    def __init__(self, parent, name, item, *args, **kwargs):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kwargs)

        self._parent = parent
        
        self._name = name
        
        self._item = item

        self.build_panel()

    @abc.abstractmethod
    def validate(self):
        pass

    @abc.abstractmethod
    def get_value(self):        
        pass

    @abc.abstractmethod
    def set_value(self,value):        
        pass
        
                
class InputDirectoryWidget(PreferencesItemWidget):
    
    type = "input_directory"

    def build_panel(self):

        sb = wx.StaticBox(self, wx.ID_ANY, label=self._item.name)
        
        self._widget = wxfile.DirBrowseButton(self, wx.ID_ANY, labelText="", startDirectory=self._item.value)
        self._widget.SetValidator(WritableDirectoryValidator())
        self._widget.SetValue(self._item.value)
        
        sizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        
        sizer.Add(self._widget, 1, wx.ALL|wx.EXPAND, 5)
                
        self.SetSizer(sizer)
    
    def get_value(self):
        
        return self._widget.GetValue()

    def set_value(self, value):
        
        self._widget.SetValue(value)

    def validate(self):

        path = PLATFORM.get_path(self._widget.GetValue())

        if PLATFORM.is_directory_writable(path):
            return True
        else:
            wx.MessageBox("The directory %r is not writable." % path, "Invalid input",wx.OK | wx.ICON_ERROR)
            return False
                        
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
                
        for item in PREFERENCES.values():
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
        applyButton = wx.Button(self, wx.ID_ANY, label="Apply")
        okButton = wx.Button(self, wx.ID_ANY, label="OK")
        
        sbSizer.Add(cancelButton, 0, wx.ALL, 5)
        sbSizer.Add((-1,-1), 1, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add(defaultButton, 0, wx.ALL, 5)
        sbSizer.Add(applyButton, 0, wx.ALL, 5)
        sbSizer.Add(okButton, 0, wx.ALL, 5)
                    
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._sizer.Add(self._notebook, 1, wx.ALL|wx.EXPAND, 5)

        self._sizer.Add(sbSizer, 0, wx.ALL|wx.EXPAND, 5)
            
        self.SetSizer(self._sizer)
                    
        self.Bind(wx.EVT_CLOSE, self.on_cancel)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancelButton)
        self.Bind(wx.EVT_BUTTON, self.on_default, defaultButton)
        self.Bind(wx.EVT_BUTTON, self.on_apply, applyButton)
        self.Bind(wx.EVT_BUTTON, self.on_ok, okButton)

    def validate(self):

        for widget in self._widgets.values():
            
            if not widget.validate():
                return False
            
        return True

    def on_apply(self,event):
        
        if not self.validate():
            return

        for k, widget in self._widgets.items():
            PREFERENCES[k].set_value(widget.get_value())

    def on_ok(self,event):
        
        if not self.validate():
            return

        for k, widget in self._widgets.items():
            PREFERENCES[k].set_value(widget.get_value())
            
        PREFERENCES.save()
        
        self.Destroy() 
                                            
    def on_cancel(self, event):
        
        self.Destroy()
        
    def on_default(self, event):
        
        for v in PREFERENCES.values():
            self._widgets[v.name].set_value(v.default)
                            
if __name__ == "__main__":
    
    app = wx.App(False)
    
    d = PreferencesSettingsDialog(None)
    
    d.ShowModal()
        
    app.MainLoop()
    
