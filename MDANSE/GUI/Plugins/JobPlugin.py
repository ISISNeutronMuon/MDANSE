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

:author: Eric C. Pellegrini
'''

import os
import subprocess               
import sys
import tempfile
import time

import wx
import wx.aui as aui

from MDANSE import PLATFORM,REGISTRY
from MDANSE.Framework.InputData.EmptyData import EmptyData

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin
from MDANSE.GUI.ComboWidgets.ConfigurationPanel import ConfigurationPanel
from MDANSE.GUI.ComboWidgets.JobHelpFrame import JobHelpFrame

class JobPlugin(ComponentPlugin):
        
    def __init__(self, parent, *args, **kwargs):
                
        self._job = REGISTRY["job"][self._type]()
        
        ComponentPlugin.__init__(self, parent, size=wx.Size(800,400), *args, **kwargs)
                
    def build_panel(self):
        
        self._main = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        self._main.SetScrollbars(pixelsPerUnitX= 20, pixelsPerUnitY=20, noUnitsX=500, noUnitsY=500)
                
        mainSizer = wx.BoxSizer(wx.VERTICAL)
                
        self._parametersPanel = ConfigurationPanel(self._main, self._job)
                    
        sb = wx.StaticBox(self._main, wx.ID_ANY)
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)

        helpButton = wx.Button(self._main, label = "Help")                                                        
        saveButton = wx.Button(self._main, label = "Save")
        runButton = wx.Button(self._main, label = "Run")

        sbSizer.Add(helpButton, 0, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add((-1,-1), 1, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add(saveButton, 0, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add(runButton, 0, wx.ALL|wx.EXPAND, 5)

        mainSizer.Add(self._parametersPanel, 1, wx.ALL|wx.EXPAND, 0)
        mainSizer.Add(sbSizer, 0, wx.ALL|wx.EXPAND, 5)

        self._main.SetSizer(mainSizer)        
        mainSizer.Layout()
        self._main.Fit()
                
        self._mgr.AddPane(self._main, aui.AuiPaneInfo().Center().Floatable(False).Dock().CaptionVisible(False).CloseButton(False))

        self._mgr.Update()
        
        self.Bind(wx.EVT_BUTTON, self.on_help, helpButton)
        self.Bind(wx.EVT_BUTTON, self.on_save, saveButton)
        self.Bind(wx.EVT_BUTTON, self.on_run, runButton)
        
    def on_help(self, event):
                                
        d = JobHelpFrame(self,self._job)

        d.Show()
                         
    def on_run(self, event=None):

        if not self._parametersPanel.validate():
            return

        parameters = self._parametersPanel.get_value() 
        
        name = self._job.define_unique_name()

        handle,filename = tempfile.mkstemp(prefix="MDANSE_%s.py" % name, text=True)
        os.close(handle)
                        
        self._job.save(filename, parameters)
                                
        if PLATFORM.name == "windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        else:
            startupinfo = None
        
        subprocess.Popen([sys.executable, filename], startupinfo=startupinfo, stdin=subprocess.PIPE,stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        time.sleep(1)

        PUBLISHER.sendMessage("msg_start_job",message=None)
        
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
                        
        self._job.save(path, parameters)

    def plug(self):
                
        self._parent._mgr.GetPane(self).Float().Center().Floatable(True).Dockable(True).CloseButton(True).BestSize((800,600))
                
        self._parent.mgr.Update()
                    
        PUBLISHER.sendMessage("msg_set_data", message=self)
                        
    def on_close(self, event):
        
        self.parent.mgr.ClosePane(self.parent.mgr.GetPane(self))
        
class JobFrame(wx.Frame):
    
    def __init__(self, parent, jobType, datakey=None):
                
        wx.Frame.__init__(self, parent, wx.ID_ANY, size = (800,800), style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)

        self._jobType = jobType

        job = REGISTRY['job'][self._jobType]
        
        self.SetTitle(job.label)
        
        data = REGISTRY['input_data'][job.ancestor[0]](datakey,True)

        self.datakey = data.name
                          
        if not isinstance(data,EmptyData):
            DATA_CONTROLLER[data.name] = data
                        
        plugin = REGISTRY['plugin'][self._jobType](self)
        
        PUBLISHER.sendMessage("msg_set_data", message=plugin)
                        
if __name__ == "__main__":
            
    filename = os.path.join(os.path.dirname(PLATFORM.package_directory()),'Data','Trajectories','MMTK','protein_in_periodic_universe.nc')
    
    app = wx.App(False)
    f = JobFrame(None,'dl_poly',filename)
    f.Show()
    app.MainLoop()            