# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/PlotterPlugin.py
# @brief     Implements module/class/test PlotterPlugin
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg

import wx
import wx.aui as wxaui

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin
from MDANSE.GUI.Plugins.Plotter1D import Plotter1D
from MDANSE.GUI.Plugins.Plotter2D import Plotter2D
from MDANSE.GUI.Plugins.Plotter3D import Plotter3D
from MDANSE.GUI.Icons import ICONS

class PlotterError(Error):
    pass

class PlotterPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.parent = parent
        self._mgr = wxaui.AuiManager(self)
        
        self.build_panel()
        self.build_layout()
        
    @property
    def dataproxy(self):
        return self.parent._data
    
    @property
    def active_plot(self):
        try :
            page = self.plot_notebook.GetPage(self.plot_notebook.GetSelection())
            return page  
        except: 
            return None
        
    def build_panel(self):
        self.plot_notebook = wxaui.AuiNotebook(self)
    
    def build_layout(self):
        self._mgr.AddPane(self.plot_notebook, wxaui.AuiPaneInfo().Center().Dock().CloseButton(False).Caption("Multiple Plot Window"))
        self._mgr.Update()

class MultiViewPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.parent = parent
 
        self.type = 'image'
        
        self.unique_slicer = None
        self.related_slicer_checkbox=None
        
        self._mgr = wxaui.AuiManager(self)
        self.Layout()

    @property
    def dataproxy(self):
        return self.parent.dataproxy

    def AddPane(self, *args, **kwds):
        self._mgr.AddPane(*args, **kwds)

    def Update(self):
        self._mgr.Update()
        
class DataPanel(wx.Panel):

    def __init__(self, parent, *args,**kwds):
        wx.Panel.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self._mgr = wxaui.AuiManager(self)
        
        self.selectedVar = None
        self.activePlot = None
        self.selectedPlot = None
        
        self.unique_slicer = None
        self.related_slicer_checkbox=None
        
        self.build_panel()
                
    def build_panel(self):    
        
        self.setup = wx.Panel(self)
        
        sizer0 =  wx.BoxSizer(wx.VERTICAL)
        
        if self.standalone:
            self.datasetlist = wx.ListCtrl(self.setup, wx.ID_ANY,style = wx.LC_REPORT|wx.LC_SINGLE_SEL)
            self.datasetlist.InsertColumn(0, 'key', width=100)
            self.datasetlist.InsertColumn(1, 'filename', width=100)
            self.datasetlist.InsertColumn(2, 'path', width=500)
            
            sizer0.Add(self.datasetlist, 1, wx.ALL|wx.EXPAND, 2)
            
            self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_dataset,  self.datasetlist) 
            self.Bind(wx.EVT_LIST_KEY_DOWN, self.delete_dataset, self.datasetlist)

        self.datalist = wx.ListCtrl(self.setup, wx.ID_ANY,style = wx.LC_REPORT|wx.LC_SINGLE_SEL)
        self.datalist.InsertColumn(0, 'Variable', width=100)
#        self.datalist.InsertColumn(1, 'Unit', width=65)
        self.datalist.InsertColumn(1, 'Axis', width=50)
        self.datalist.InsertColumn(2, 'Dimension')
        self.datalist.InsertColumn(3, 'Size')
        
        sizer1 =  wx.BoxSizer(wx.HORIZONTAL)
       
        self.plot_type_label = wx.StaticText(self.setup, label="Select Plotter")
        self.plotter_list = {'Line':1, 'Image':2, 'Elevation':2,'Iso-Surface':3,'Scalar-Field':3}
        self.plot_type  = wx.ComboBox(self.setup, style=wx.CB_READONLY)
        
        sizer1.Add(self.plot_type_label, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer1.Add(self.plot_type, 1, wx.ALIGN_CENTER_VERTICAL)
        
        sizer2 =  wx.BoxSizer(wx.HORIZONTAL)
        
        self.plot_button  = wx.Button(self.setup, wx.ID_ANY, label="Plot in new window")
        self.replot_button  = wx.Button(self.setup, wx.ID_ANY, label="Plot in current figure")
        
        sizer2.Add(self.plot_button, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        sizer2.Add(self.replot_button, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        sizer0.Add(self.datalist, 2, wx.ALL|wx.EXPAND, 2)
        sizer0.Add(sizer1, 0, wx.ALL|wx.EXPAND, 2)
        sizer0.Add(sizer2, 0, wx.ALL|wx.EXPAND, 2)
        
        self.setup.SetSizer(sizer0)        
        sizer0.Fit(self.setup)
        self.setup.Layout()
        
        qviewPanel = wx.Panel(self)
        sb_sizer2 =  wx.BoxSizer(wx.VERTICAL)
                      
        self.qvFigure = Figure(figsize=(1,1))
        self.qvCanvas = FigureCanvasWxAgg(qviewPanel, wx.ID_ANY, self.qvFigure)
        self.qvPlot = self.qvFigure.add_axes([0.01,0.01,0.98,0.98])
        sb_sizer2.Add(self.qvCanvas, 1, wx.ALL|wx.EXPAND, 2)
        
        qviewPanel.SetSizer(sb_sizer2)        
        sb_sizer2.Fit(qviewPanel)
        qviewPanel.Layout()
        
        self._mgr.AddPane(qviewPanel,wxaui.AuiPaneInfo().Dock().Bottom().Floatable(False).CloseButton(False).Caption("Quick View").MinSize((300,300)))
        self._mgr.AddPane(self.setup,wxaui.AuiPaneInfo().Dock().Center().Floatable(False).CloseButton(False).Caption("Data"))
        
        self._mgr.Update()

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_select_variables,  self.datalist) 
        self.Bind(wx.EVT_BUTTON, self.on_plot, self.plot_button)
        self.Bind(wx.EVT_BUTTON, self.on_replot, self.replot_button)
        
    @property
    def dataDict(self):
        if self.standalone:
            return self.parent._dataDict
        else:
            return None
    
    @property
    def standalone(self):
        return self.parent.standalone
        
    @property
    def dataproxy(self):
        return self.parent._data
    
    @property
    def plotterPanel(self):
        return self.parent._plotterPanel
    
    @property
    def plotterNotebook(self):
        return self.parent._plotterPanel.plot_notebook
   
    def delete_dataset(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            dataset = self.datasetlist.GetItemText(self.datasetlist.GetFocusedItem())
            self.dataDict.pop(dataset)
            self.datasetlist.DeleteItem(self.datasetlist.GetFocusedItem())
            self.datalist.DeleteAllItems()
            self.datasetlist.Select(0,1) 
            
    def on_select_dataset(self, event):
        if event is None:
            return
        currentItem = event.m_itemIndex
        var = self.datasetlist.GetItemText(currentItem)
        self.parent._data = self.dataDict[var]['data']
        self.show_data()
        
    def show_dataset(self, index=0):
        self.datasetlist.DeleteAllItems()
        for i, k in enumerate(self.dataDict.keys()):
            self.datasetlist.InsertStringItem(i, k)
            self.datasetlist.SetStringItem(i, 1,self.dataDict[k]['basename'])
            self.datasetlist.SetStringItem(i, 2,self.dataDict[k]['path'])
        self.datasetlist.Select(index, True)
        
    def show_data(self):
        self.datalist.DeleteAllItems()
        for i, var in enumerate(sorted(self.dataproxy.keys())):
            self.datalist.InsertStringItem(i, var)
            #self.datalist.SetStringItem(i, 1,self.dataproxy[var]['units'])
            axis = ','.join(self.dataproxy[var]['axis'])
            self.datalist.SetStringItem(i, 1,axis)
            self.datalist.SetStringItem(i, 2,str(self.dataproxy[var]['data'].ndim))
            self.datalist.SetStringItem(i, 3,str(self.dataproxy[var]['data'].shape))
        self.datalist.Select(0, True)
            
    def on_select_variables(self, event = None):
        if event is None:
            return
        currentItem = event.m_itemIndex
        var = self.datalist.GetItemText(currentItem)
        data = self.dataproxy[var]['data']
        ndim = data.ndim
        self.plot_type.Clear()
        types = []
        for _type, req_dim in self.plotter_list.items():
            if ndim == req_dim:
                types += [_type]
        self.plot_type.SetItems(types)
        if not self.plot_type.IsEmpty():            
            self.plot_type.SetStringSelection(types[-1])

        self.selectedVar = var
        self.plot_quickview(data)            
    
    def plot_quickview(self, data):
        self.qvPlot.clear()
        ndim = data.ndim

        if ndim == 1:
            self.qvPlot.plot(data)
            self.qvFigure.gca().legend((self.selectedVar,None), loc = 'best', frameon = True, shadow = True, fancybox = False) 
        elif ndim == 2:
            self.qvPlot.imshow(data.T, interpolation='nearest', origin='lower')
            
        else:
            self.qvPlot.text(0.1, 0.5, 'No QuickView for data with dimension > 2 ')
        self.qvPlot.set_aspect('auto')

        self.qvCanvas.draw()

    def on_plot(self, event=None):
        if self.selectedVar is None:
            return
        
        data = self.dataproxy[self.selectedVar]['data']
        plot_type = self.plot_type.GetValue()
        if plot_type == 'Line':
            Plotter = Plotter1D(self)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.plot(data, self.selectedVar)
            
        elif plot_type == 'Image':
            Plotter = Plotter2D(self)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.plot(data, self.selectedVar)
            
        elif plot_type == 'Elevation':
            Plotter = Plotter3D(self.parent)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.elevation(data)
            
        elif plot_type == 'Iso-Surface':
            Plotter = Plotter3D(self.parent)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.isosurface(data,data.mean(), 'w')
            
        elif plot_type == 'Scalar-Field':
            Plotter = Plotter3D(self.parent)
            self.plotterNotebook.AddPage(Plotter, "%s(%s)"%(self.selectedVar,plot_type))
            Plotter.scalarfield(data)
        else :
            raise PlotterError("Unrecognized plotter type : %s"%plot_type)
        
    def on_replot(self, event=None):
        self.selectedPlot = self.plotterPanel.active_plot
        
        if self.selectedPlot is None:
            return
        
        plot_type = self.plot_type.GetValue()
        if plot_type == 'Line' and self.selectedPlot.type == 'line':     
            data = self.dataproxy[self.selectedVar]['data']
            self.selectedPlot.plot(data, self.selectedVar)
            
        if plot_type == 'Image' and self.selectedPlot.type == 'image': 
            data = self.dataproxy[self.selectedVar]['data']
            if hasattr(self.selectedPlot, 'AddPane'):
                Plotter = Plotter2D(self.selectedPlot)
                Plotter.plot(data, self.selectedVar)
                self.selectedPlot.AddPane(Plotter, wxaui.AuiPaneInfo().Right().CloseButton(True).CaptionVisible(True).Caption(self.selectedVar).MinSize((200,-1)))
                self.selectedPlot.Update()
            else:
                li_idx = self.plotterNotebook.GetPageIndex(self.selectedPlot)
                
                multiplot = MultiViewPanel(self)
                
                NewPlotter = Plotter2D(multiplot)
                NewPlotter.plot(data, self.selectedVar)
                
                OldPlotter = Plotter2D(multiplot)
                OldPlotter.replot(self.selectedPlot)

                multiplot.AddPane(NewPlotter, wxaui.AuiPaneInfo().Right().CloseButton(True).CaptionVisible(True).Caption(self.selectedVar).MinSize((200,-1)))
                multiplot.AddPane(OldPlotter, wxaui.AuiPaneInfo().Center().CloseButton(True).CaptionVisible(True).Caption(self.selectedPlot.varname))
                multiplot.Update()
                
                self.selectedPlot.Destroy()
                self.selectedPlot = None
                self.plotterNotebook.RemovePage(li_idx)
                self.plotterNotebook.AddPage(multiplot, '*MultiView*(Image)', select=True)
       
class PlotterPlugin(ComponentPlugin):
    
    label = "2D/3D Plotter"
    
    ancestor = ["netcdf_data"]
    
    category = ("Plotter",)
    
    def __init__(self, parent, mode='embeded'):
        
        self.standalone = False
        
        if mode == 'standalone':
            self.make_standalone()
        
        ComponentPlugin.__init__(self,parent)
        
    def build_panel(self):
        self._dataPanel = DataPanel(self)
        self._plotterPanel = PlotterPanel(self)
        
        self._mgr.AddPane(self._dataPanel, wxaui.AuiPaneInfo().Dock().Left().Floatable(False).CloseButton(False).CaptionVisible(False).MinSize((300,-1)))
        self._mgr.AddPane(self._plotterPanel, wxaui.AuiPaneInfo().Center().Dock().Floatable(False).CloseButton(False).CaptionVisible(False))
    
    def make_standalone(self):
        self.standalone = True
        self._dataDict = collections.OrderedDict()
        
    def plug(self):
        self._data = self.dataproxy.data
        self._dataPanel.show_data()

        self._parent._mgr.GetPane(self).Dock().Floatable(False).Center().CloseButton(True).Caption("2D/3D Plotter")
        self._parent._mgr.Update()

class PlotterFrame(wx.Frame):
    
    def __init__(self, parent, title="2D/3D Plotter"):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)
        self.__build_dialog()
        self.__build_menu()
 
    def __build_menu(self):
        mainMenu = wx.MenuBar()
        fileMenu = wx.Menu()
        loadData = fileMenu.Append(wx.ID_ANY, 'Load')

        mainMenu.Append(fileMenu, 'File')

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(ICONS["plot",32,32])        
        self.SetIcon(icon) 
        
        self.SetMenuBar(mainMenu)
        
        self.Bind(wx.EVT_MENU, self.on_load_data, loadData)
   
    def on_quit(self, event=None):

        self.Destroy()
                
    def on_load_data(self, event=None):
        
        filters = 'NC file (*.nc)|*.nc|All files (*.*)|*.*'
        dialog = wx.FileDialog ( self, message = 'Open file...', wildcard=filters, style=wx.MULTIPLE)
        if dialog.ShowModal() == wx.ID_CANCEL:
            return
        
        baselist = dialog.GetFilenames()
        filelist = dialog.GetPaths()
        
        for i in range(len(filelist)):
            basename = baselist[i]    
            filename = filelist[i]
            
            f = NetCDFFile(filename,"r")
            _vars = f.variables
            data = collections.OrderedDict()
            for k in _vars:
                data[k]={}
                if hasattr(_vars[k], 'axis'):
                    if _vars[k].axis:
                        data[k]['axis'] =  _vars[k].axis.split('|')
                    else:
                        data[k]['axis'] = []
                else:
                    data[k]['axis'] = []
                data[k]['data'] = _vars[k].getValue()
                data[k]['units'] = getattr(_vars[k],"units","au")
            
            unique_name = self.unique(basename, self.plugin._dataDict)
            
            self.plugin._dataDict[unique_name]={'data':data,'path':filename,'basename':basename}
            self.plugin._dataPanel.show_dataset(-1)
    
    def unique(self, key, dic):
        skey = key
        i = 0
        while key in dic.keys():
            key = skey + '_%d'%i
            i += 1
        return key 
    
    def __build_dialog(self):
        mainPanel = wx.Panel(self, wx.ID_ANY)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.plugin = PlotterPlugin(mainPanel, 'standalone')
         
        mainSizer.Add(self.plugin, 1, wx.ALL|wx.EXPAND, 5)

        mainPanel.SetSizer(mainSizer)        
        mainSizer.Fit(mainPanel)
        mainPanel.Layout()

        self.SetSize((1000, 700))

REGISTRY["plotter"] = PlotterPlugin

if __name__ == "__main__":
    app = wx.App(False)
    f = PlotterFrame(None)
    f.Show()
    app.MainLoop()
    
