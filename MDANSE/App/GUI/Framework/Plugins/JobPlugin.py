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
Created on Apr 14, 2015

@author: Eric C. ellegrini
'''

import os
import subprocess               
import sys
import tempfile
import time

import wx
import wx.aui as aui

from MDANSE import PLATFORM,REGISTRY
from MDANSE.Externals.pubsub import pub

from MDANSE.App.GUI.ComboWidgets.ConfigurationPanel import ConfigurationPanel
from MDANSE.App.GUI.Framework.Plugins.ComponentPlugin import ComponentPlugin
from MDANSE.App.GUI.ComboWidgets.JobHelpFrame import JobHelpFrame

class JobPlugin(ComponentPlugin):
        
    def __init__(self, parent, *args, **kwargs):
                
        self._job = REGISTRY["job"][self.type]()
        
        ComponentPlugin.__init__(self, parent, size=wx.Size(800,400), *args, **kwargs)
                
    def build_panel(self):
        
        self._main = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        self._main.SetScrollbars(pixelsPerUnitX= 20, pixelsPerUnitY=20, noUnitsX=500, noUnitsY=500)
                
        mainSizer = wx.BoxSizer(wx.VERTICAL)
                
        self._parametersPanel = ConfigurationPanel(self._main, self._job)
                    
        sb = wx.StaticBox(self._main, wx.ID_ANY)
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)

        cancelButton = wx.Button(self._main, label = "Cancel")                                                        
        helpButton = wx.Button(self._main, label = "Help")                                                        
        saveButton = wx.Button(self._main, label = "Save")
        runButton = wx.Button(self._main, label = "Run")

        sbSizer.Add(cancelButton, 0, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add((-1,-1), 1, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add(helpButton, 0, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add(saveButton, 0, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add(runButton, 0, wx.ALL|wx.EXPAND, 5)

        mainSizer.Add(self._parametersPanel, 1, wx.ALL|wx.EXPAND, 0)
        mainSizer.Add(sbSizer, 0, wx.ALL|wx.EXPAND, 5)

        self._main.SetSizer(mainSizer)        
        mainSizer.Layout()
        self._main.Fit()
                
        self._mgr.AddPane(self._main, aui.AuiPaneInfo().Center().Floatable(False).Dock().CaptionVisible(False).CloseButton(False))

        self._mgr.Update()
        
        self.Bind(wx.EVT_BUTTON, self.on_close, cancelButton)
        self.Bind(wx.EVT_BUTTON, self.on_help, helpButton)
        self.Bind(wx.EVT_BUTTON, self.on_save, saveButton)
        self.Bind(wx.EVT_BUTTON, self.on_run, runButton)
        
    def on_help(self, event):
                                
        d = JobHelpFrame(self,self._job)

        d.Show()
                         
    def on_run(self, event=None):

        parameters = self._parametersPanel.get_value()
        
        t = tempfile.mkstemp(prefix = "MDANSE_%s_" % self._job.type, text = True)
        os.close(t[0])
                
        self._job.save_job(t[1], parameters)
                
        self._job.configuration.set_parameters(parameters)
                
        self._job.configuration.configure()
                
        if PLATFORM.name == "windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None
        
        subprocess.Popen([sys.executable, t[1]], startupinfo=startupinfo)

        time.sleep(1)

        pub.sendMessage("on_start_job",message=None)
        
    def on_save(self, event=None):

        if not self._parametersPanel.validate():
            return

        parameters = self._parametersPanel.get_value()
        
        d = wx.FileDialog(self, "Save MDANSE python script", style = wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT, wildcard = "Python files (*.py)|*.py")
        
        if d.ShowModal() == wx.ID_CANCEL:
            return
        
        path = d.GetPath().strip()
                
        if not path:
            return
        
        if os.path.splitext(path)[1] != ".py":
            path += ".py"
                        
        self._job.save_job(path, parameters)

    def plug(self):
        
        pub.sendMessage("on_set_data", message = (self,self.datakey))
        
        self._parent._mgr.GetPane(self).Float().Center().Dockable(False).CloseButton(True).BestSize((800,600))

        self._parent.mgr.Update()
                        
    def on_close(self, event):
        
        self.parent.mgr.ClosePane(self.parent.mgr.GetPane(self))
        
class JobFrame(wx.Frame):
    
    def __init__(self, parent, jobType):
                
        wx.Frame.__init__(self, parent, wx.ID_ANY, size = (800,400), style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)

        self._jobType = jobType

        self.build_dialog()

    def build_dialog(self):
                
        mainPanel = wx.Panel(self, wx.ID_ANY, size = self.GetSize())
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self._jobPlugin = REGISTRY['plugin'][self._jobType](mainPanel, wx.ID_ANY)
                
        mainSizer.Add(self._jobPlugin, 1, wx.ALL|wx.EXPAND)

        mainPanel.SetSizer(mainSizer)        
        mainSizer.Fit(mainPanel)
        mainPanel.Layout()
        
        self.SetTitle("Run %s job" % self._jobPlugin._job.label)
        
        self.Bind(wx.EVT_CLOSE, self.on_quit)
        
    def on_quit(self, event):
        
        d = wx.MessageDialog(None,
                             'Do you really want to quit ?',
                             'Question',
                             wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()           
        
if __name__ == "__main__":
    app = wx.App(False)
    f = JobFrame(None,'discover')
    f.Show()
    app.MainLoop()            