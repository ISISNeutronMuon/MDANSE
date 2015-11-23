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
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

import os

import wx
import wx.aui as wxaui
import wx.grid as wxgrid
from wx.lib.delayedresult import startWorker

from MDANSE import LOGGER, REGISTRY
from MDANSE.Framework.Plugins.UserDefinitionPlugin import UserDefinitionPlugin
from MDANSE.GUI.ComboWidgets.ConfigurationPanel import ConfigurationPanel
from MDANSE.GUI.ComboWidgets.ProgressBar import ProgressBar

class QVectorsData(wxgrid.PyGridTableBase):
    
    def __init__(self, data=None):
        
        wxgrid.PyGridTableBase.__init__(self)

        self._colLabels = ["Qx","Qy","Qz","|Q|","h","k","l"]
        
        self._data=data
           
        self._grid = []                     
        if self._data is not None:
            
            for v in self._data.values():

                if not v:
                    continue

                for i in range(v["n_q_vectors"]):
                    temp = []
                    temp.extend(["%8.3f" % val for val in v["q_vectors"][:,i]])
                    temp.extend(["%8.3f" % v["q"]])
                    if v["hkls"] is not None:
                        temp.extend(["%d" % val for val in v["hkls"][:,i]])
                    else:
                        temp.extend(['-']*3)
                
                    self._grid.append(temp)
                    
    @property
    def data(self):
        return self._data

    def GetAttr(self, row, col, kind):
        
        attr = wxgrid.GridCellAttr()
        attr.SetBackgroundColour(wx.NamedColour("LIGHT BLUE"))
        if col == 3:
            attr.SetTextColour(wx.RED)
        attr.SetReadOnly(True)
        attr.SetAlignment(wx.ALIGN_RIGHT,wx.ALIGN_CENTRE)
        
        return attr        
                            
    def GetNumberRows(self):
        
        return len(self._grid)
                
    def GetNumberCols(self):

        return 7

    def GetColLabelValue(self, col):
        
        return self._colLabels[col]
                    
    def GetRowLabelValue(self, row):
        return row+1
        
    def GetValue(self, row, col):
        
        if self._grid is None:
            return "-"
        else:
            return self._grid[row][col]
                    
    def SetValue(self, row, col, value):
        pass
                            
class QVectorsPanel(wx.Panel):
    
    def __init__(self, generator,parameters,*args, **kwargs):
                                        
        wx.Panel.__init__(self, *args, **kwargs)
                
        self._generator = generator
        self._parameters = parameters
                
        self._grid = wxgrid.Grid(self)
        self._grid.DisableCellEditControl()
        
        self._progress = ProgressBar(self)
                
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._grid, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self._progress, 0, wx.ALL|wx.EXPAND, 5)
                
        self.SetSizer(sizer)

    @property
    def grid(self):
        
        return self._grid

    @property
    def generator(self):
        
        return self._generator

    @property
    def parameters(self):
        
        return self._parameters

    @property
    def progress(self):
        
        return self._progress
                            
class QVectorsPlugin(UserDefinitionPlugin):
    
    type = 'q_vectors'

    label = "Q vectors"
    
    ancestor = ["mmtk_trajectory"]
            
    def __init__(self, parent, *args, **kwargs):

        self._currentGenerator = None

        self._value = None
                        
        UserDefinitionPlugin.__init__(self, parent,size=(800,700))
                                                                          
    def build_panel(self):   

        sizer = wx.BoxSizer(wx.VERTICAL)
                 
        # Widgets and sizers related to generator section        
        self._mainPanel = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        self._mainPanel.SetScrollbars(20,20,50,50)
        sb1 = wx.StaticBox(self._mainPanel, wx.ID_ANY, label="generator")
        sbSizer1 = wx.StaticBoxSizer(sb1, wx.VERTICAL)
        self._availableGenerators = wx.Choice(self._mainPanel, wx.ID_ANY)
        generateButton  = wx.Button(self._mainPanel, wx.ID_ANY, label="Generate")
        sbSizer1.Add(self._availableGenerators, 1, wx.ALL|wx.EXPAND, 5)        
        sbSizer1.Add(generateButton, 1, wx.ALL|wx.EXPAND, 5)        
        sizer.Add(sbSizer1, 0, wx.ALL|wx.EXPAND, 5)
    
        # Widgets and sizers related to parameters section        
        sb2 = wx.StaticBox(self._mainPanel, wx.ID_ANY, label="parameters")
        self._parametersSizer = wx.StaticBoxSizer(sb2, wx.VERTICAL)
        sizer.Add(self._parametersSizer, 0, wx.ALL|wx.EXPAND, 5)

        self._notebook = wxaui.AuiNotebook(self._mainPanel, wx.ID_ANY, style=wxaui.AUI_NB_DEFAULT_STYLE&~wxaui.AUI_NB_TAB_MOVE)

        sizer.Add(self._notebook, 3, wx.ALL|wx.EXPAND, 5)
                 
        self._mainPanel.SetSizer(sizer)

        self._mgr.AddPane(self._mainPanel, wxaui.AuiPaneInfo().DestroyOnClose().Center().Dock().CaptionVisible(False).CloseButton(False).BestSize(self.GetSize()))
        self._mgr.Update()
                                 
        self.Bind(wxaui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_close_tab, self._notebook)
        self.Bind(wx.EVT_BUTTON, self.on_generate_q_vectors, generateButton)
        self.Bind(wx.EVT_CHOICE, self.on_select_generator, self._availableGenerators)

    def plug(self):
        
        self.parent.mgr.GetPane(self).Float().Dockable(False).CloseButton(True).BestSize((600,600))
        
        self.parent.mgr.Update()
        
        self.set_trajectory(self.dataproxy.data)

    def set_trajectory(self,trajectory):

        self._trajectory = trajectory 

        self._target = os.path.basename(self._trajectory.filename)

        if self._trajectory.universe.is_periodic:
            choices = REGISTRY["q_vectors"].keys()
        else:
            choices = [k for k,v in REGISTRY["q_vectors"].items() if not v.is_lattice]        
        self._availableGenerators.SetItems(choices)
        self._availableGenerators.SetSelection(0)

        self.select_generator(self._availableGenerators.GetStringSelection())
                
    def on_close(self, event):
        
        self.Destroy()
        
    def on_close_tab(self, event):

        qPanel = event.GetEventObject().GetPage(event.GetSelection())
        if qPanel.progress.is_running():
            d = wx.MessageDialog(None, 'The background task is still running. You must cancel it before closing this tab.', 'Warning', wx.OK|wx.ICON_WARNING)
            d.ShowModal()
            event.Veto()
            return            
                    
    def generate_q_vectors(self,generator):
                                
        generator.generate()
                         
        return generator['q_vectors']
    
    def generate_q_vectors_done(self,result,qPanel):
                
        data = result.get()
        if data:
            table = QVectorsData(data)
            qPanel.grid.SetTable(table)
            qPanel.grid.Refresh()
        
    def on_generate_q_vectors(self, event):

        generator = self._availableGenerators.GetStringSelection()
        generator = REGISTRY["q_vectors"][generator](self._trajectory.universe)
        parameters = self._configurationPanel.get_value()
        generator.setup(parameters)
        
        qPanel = QVectorsPanel(generator,parameters,self._mainPanel,wx.ID_ANY)
        self._notebook.AddPage(qPanel, "Q Vectors")
        
        generator.setStatus(qPanel.progress)
                
        startWorker(self.generate_q_vectors_done, self.generate_q_vectors, cargs=(qPanel,),wargs=(generator,))                                          
                
    def on_select_generator(self, event):
                                
        self.select_generator(event.GetString())
            
    def validate(self):

        if self._notebook.GetPageCount() == 0:
            LOGGER("No Q vectors generated.", "error")
            return

        qPanel = self._notebook.GetPage(self._notebook.GetSelection())

        if qPanel._grid.GetTable().data is None:
            LOGGER("No data is the selected Q vectors tab", "error")
            return
        
        ud = {}
        ud['parameters'] = (qPanel.generator.type,qPanel.parameters)
        ud['generator'] = qPanel.generator.type
        ud['q_vectors'] = qPanel.grid.GetTable().data
        ud['is_lattice'] = qPanel.generator.is_lattice
        
        if not ud['q_vectors']:
            LOGGER("No Q vectors generated.", "error", ["dialog"])
            return None
        
        return ud
                
    def select_generator(self, generatorName):
                         
        if generatorName == self._currentGenerator:
            return
                                       
        self._currentGenerator = REGISTRY["q_vectors"][generatorName](self._trajectory.universe)
         
        self._parametersSizer.Clear(deleteWindows=True)
 
        self.Freeze()
                 
        self._configurationPanel = ConfigurationPanel(self._mainPanel, self._currentGenerator)
 
        self._parametersSizer.Add(self._configurationPanel, 1, wx.ALL|wx.EXPAND, 5)
                                         
        self.Thaw()
                         
        self._parametersSizer.Layout()
        
        self._mgr.Update()
        