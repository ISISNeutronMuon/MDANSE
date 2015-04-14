import abc
import os
import threading

import wx
import wx.aui as aui
import wx.grid
from wx.lib.delayedresult import startWorker

from nMOLDYN import LOGGER, REGISTRY, USER_DEFINITIONS
from nMOLDYN.Core.Status import Status
from nMOLDYN.Externals.pubsub import pub as Publisher
from nMOLDYN.Framework.Configurators.Configurators import ConfiguratorError
from nMOLDYN.Framework.Plugins.Plugin import DataPlugin, ComponentPlugin, plugin_parent
from nMOLDYN.GUI.Resources.Icons import ICONS, scaled_bitmap
from nMOLDYN.GUI.Widgets.ConfigurationPanel import ConfigurationPanel
from nMOLDYN.GUI.Widgets.ProgressBar import ProgressBar

class QVectorsData(wx.grid.PyGridTableBase):
    
    def __init__(self, data=None):
        
        wx.grid.PyGridTableBase.__init__(self)

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
        
        attr = wx.grid.GridCellAttr()
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
                
        self._grid = wx.grid.Grid(self)
        self._grid.DisableCellEditControl()
        
        self._progress = ProgressBar(self)

        udPanel = wx.Panel(self, wx.ID_ANY)
        udSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._udName = wx.TextCtrl(udPanel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self._saveButton  = wx.Button(udPanel, wx.ID_ANY, label="Save")
        udSizer.Add(self._udName, 1, wx.ALL|wx.EXPAND, 5)
        udSizer.Add(self._saveButton, 0, wx.ALL, 5)
        udPanel.SetSizer(udSizer)
                
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._grid, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self._progress, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(udPanel, 0, wx.ALL|wx.EXPAND, 5)
                
        self.SetSizer(sizer)
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.on_save_parameters, self._saveButton)
        
    @property
    def grid(self):
        
        return self._grid

    def on_save_parameters(self, event):
        
        if self._grid.GetTable().data is None:
            LOGGER("No Q vectors generated", "error")
            return

        plugin = plugin_parent(self)
                    
        if plugin._trajectory is None:
            LOGGER("No trajectory loaded", "error", ["dialog"])
            return

        name = self._udName.GetValue()

        if not name:
            LOGGER("You must enter a value for the user definition", "error", ["dialog"])
            return
        
        target = os.path.basename(plugin._trajectory.filename)
        
        ud = REGISTRY['userdefinable']['q_vectors'](target,
                                                    generator=self._generator.type,
                                                    parameters=self._parameters,
                                                    q_vectors=self._grid.GetTable().data,
                                                    is_lattice=self._generator.is_lattice)
        
        USER_DEFINITIONS[name] = ud
        USER_DEFINITIONS.save()
        
        Publisher.sendMessage("new_q_vectors", message = (target, name))

    @property
    def parameters(self):
        
        return self._parameters

    @property
    def progress(self):
        
        return self._progress
    
    @property
    def saveButton(self):
        
        return self._saveButton
        
    @property
    def udName(self):
        
        return self._udName
        
class QVectorsPlugin(ComponentPlugin):
    
    type = "q_vectors"
    
    label = "Q Vectors"
    
    ancestor = "mmtk_trajectory"
    
    category = ("Q vectors",)
        
    def __init__(self, parent, **kwargs):

        self._currentGenerator = None

        self._value = None
        
        self._trajectory = None
        
        ComponentPlugin.__init__(self, parent, size=(-1,50), **kwargs)
                                                          
    def build_panel(self):   
 
        self._mainPanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
        
        self._mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self._notebook = aui.AuiNotebook(self._mainPanel, wx.ID_ANY, style=aui.AUI_NB_DEFAULT_STYLE^aui.AUI_NB_TAB_MOVE)

        self._parametersPanel = wx.ScrolledWindow(self._mainPanel)
        self._parametersPanel.SetScrollbars(1,1,40,40)

        vSizer = wx.BoxSizer(wx.VERTICAL)
        
        sb = wx.StaticBox(self._parametersPanel, wx.ID_ANY, label="generator")
        sbSizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self._generatorsChoice = wx.Choice(self._parametersPanel, wx.ID_ANY)
        generateButton  = wx.Button(self._parametersPanel, wx.ID_ANY, label="Generate")
        sbSizer.Add(self._generatorsChoice, 1, wx.ALL|wx.EXPAND, 5)        
        sbSizer.Add(generateButton, 1, wx.ALL|wx.EXPAND, 5)        
        vSizer.Add(sbSizer, 0, wx.ALL|wx.EXPAND, 5)

        self._parametersWidgets = ['',{}]
        sb = wx.StaticBox(self._parametersPanel, wx.ID_ANY, label="parameters")
        self._parametersSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)        
        vSizer.Add(self._parametersSizer, 1, wx.ALL|wx.EXPAND, 5)

        self._parametersPanel.SetSizer(vSizer)
        
        self._notebook.AddPage(self._parametersPanel, "parameters")
        
        self._mainSizer.Add(self._notebook, 1, wx.ALL|wx.EXPAND, 5)
        
        self._mainPanel.SetSizer(self._mainSizer)
                
        self._mgr.AddPane(self._mainPanel, aui.AuiPaneInfo().Center().Dock().CaptionVisible(False).CloseButton(False))

        self._mgr.Update()
        
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_close_tab, self._notebook)
        self.Bind(wx.EVT_BUTTON, self.on_generate_q_vectors, generateButton)
        self.Bind(wx.EVT_CHOICE, self.on_select_generator, self._generatorsChoice)
                
    def on_close(self, event):
        
        self.parent.mgr.ClosePane(self.parent.mgr.GetPane(self))
        
    def on_close_tab(self, event):
        
        if event.GetSelection() == 0:
            event.Veto()
        else:
            qPanel = event.GetEventObject().GetPage(event.GetSelection())
            if qPanel.progress.status.is_running():
                d = wx.MessageDialog(None, 'The background task is still running. You must cancel it before closing this tab.', 'Warning', wx.OK|wx.ICON_WARNING)
                d.ShowModal()
                event.Veto()
                return            
                    
    def generate_q_vectors(self,generator,status):
                                
        data = generator.run(status)
                 
        return data
    
    def generate_q_vectors_done(self,result,qPanel):
                
        data = result.get()
        if data:
            table = QVectorsData(data)
            qPanel.grid.SetTable(table)
            qPanel.grid.Refresh()
            qPanel.udName.Enable()
            qPanel.saveButton.Enable()
        
    def on_generate_q_vectors(self, event):

        generator = self._generatorsChoice.GetStringSelection()
        generator = REGISTRY["qvectors"][generator](self._trajectory.universe)
        parameters = self._configurationPanel.get_value()
        generator.configure(parameters)
        
        qPanel = QVectorsPanel(generator,parameters,self._mainPanel,wx.ID_ANY)
        self._notebook.AddPage(qPanel, "Q Vectors")
        
        qPanel.udName.Disable()
        qPanel.saveButton.Disable()
        
        startWorker(self.generate_q_vectors_done, self.generate_q_vectors, cargs=(qPanel,),wargs=(generator,qPanel.progress.status))                                          
                
    def on_select_generator(self, event):
                                
        self.select_generator(event.GetString())
                
    def set_generators(self):

        if self._trajectory.universe.is_periodic:
            choices = REGISTRY["qvectors"].keys()
        else:
            choices = [k for k,v in REGISTRY["qvectors"].items() if not v.is_lattice]
        
        self._generatorsChoice.SetItems(choices)
        self._generatorsChoice.SetSelection(0)

    def plug(self):

        self._trajectory = self.dataproxy.data
        
        self.set_generators()        
         
        self.select_generator(self._generatorsChoice.GetStringSelection())

        self._parent._mgr.GetPane(self).Float().CloseButton(True).BestSize((600,600))            
        self._parent._mgr.Update()
                
    def select_generator(self, generatorName):
                        
        if generatorName == self._currentGenerator:
            return
                              
        self._currentGenerator = REGISTRY["qvectors"][generatorName](self._trajectory.universe)
        
        self._parametersSizer.Clear(deleteWindows=True)

        self.Freeze()
                
        self._configurationPanel = ConfigurationPanel(self._parametersPanel, self._currentGenerator.configuration)

        self._parametersSizer.Add(self._configurationPanel, 1, wx.ALL|wx.EXPAND, 5)
                                
        self.Thaw()
                        
        self._parametersSizer.Layout()
                
        self._mainPanel.Fit()
        
        self._mgr.Update()        

if __name__ == "__main__":
    
    from MMTK.Trajectory import Trajectory
    
    t = Trajectory(None,"../../../UserData/Trajectories/mmtk/protein_in_periodic_universe.nc","r")
    
    app = wx.App(False)
    
    f = wx.Frame(None,size=(1000,500))
    
    mgr = aui.AuiManager(f)
    
    p = QVectorsPlugin(f)

    mgr.AddPane(p, aui.AuiPaneInfo().Caption("Data").Name("data").Left().CloseButton(True).DestroyOnClose(False).MinSize((250,-1)))
    
    mgr.Update()
    
    p._trajectory = t
    
    p.set_generators()
    
    p.select_generator(p._generatorsChoice.GetStringSelection())
    
    f.Show()
    
    app.MainLoop()
    
    