# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/InstrumentResolutionWidget.py
# @brief     Implements module/class/test InstrumentResolutionWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import wx

from MDANSE import REGISTRY
from MDANSE.GUI.Widgets.IWidget import IWidget
from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.ComboWidgets.ConfigurationPanel import ConfigurationPanel

class InstrumentResolutionDialog(wx.Dialog):
    
    def __init__(self, parent=None, nSteps=100, timeStep=1.0):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Instrument resolution", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)

        self._parent = parent

        self._nSteps = nSteps
        
        self._timeStep = timeStep
        
        self._omegas = 2.0*numpy.pi*numpy.fft.fftshift(numpy.fft.fftfreq(self._nSteps,timeStep))
                
        self._currentKernel = None
                          
        self._value = None
                                
        self.build_dialog()
        
    def build_dialog(self):

        sizer = wx.GridBagSizer(5,5)
        
        sb = wx.StaticBox(self, wx.ID_ANY, label="kernel")
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        self._kernelChoice = wx.Choice(self, wx.ID_ANY, choices=list(REGISTRY["instrument_resolution"].keys()))
        self._kernelChoice.SetSelection(0)
        sbSizer.Add(self._kernelChoice, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(sbSizer, (0,0), flag=wx.EXPAND)

        self._parametersWidgets = ['',{}]
        sb = wx.StaticBox(self, wx.ID_ANY, label="parameters")
        self._parametersSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)        
        sizer.Add(self._parametersSizer, (1,0), flag=wx.EXPAND)

        sb = wx.StaticBox(self, wx.ID_ANY)
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        self._cancel = wx.Button(self, wx.ID_ANY, label="Discard and quit")
        self._plot = wx.Button(self, wx.ID_ANY, label="Plot")
        self._ok = wx.Button(self, wx.ID_ANY, label="Save and quit")
        sbSizer.Add(self._cancel, 0, wx.ALL, 5)
        sbSizer.Add((-1,-1), 1, wx.ALL|wx.EXPAND, 5)
        sbSizer.Add(self._plot, 0, wx.ALL, 5)
        sbSizer.Add(self._ok, 0, wx.ALL, 5)
        sizer.Add(sbSizer, (2,0), span=(1,2), flag=wx.EXPAND)

        sb = wx.StaticBox(self, wx.ID_ANY, label="plot")
        sbSizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self._dpi = 100
        self._figure = Figure((5.0, 4.0), dpi=self._dpi)
        self._canvas = FigCanvas(self, -1, self._figure)
        self._axis = self._figure.add_subplot(111)
        self._toolbar = NavigationToolbar(self._canvas)
        sbSizer.Add(self._canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        sbSizer.Add(self._toolbar, 0, wx.EXPAND)
        sizer.Add(sbSizer, (0,1),span=(2,1), flag=wx.EXPAND)
        
        sizer.AddGrowableRow(1)
        sizer.AddGrowableCol(1)
        
        self.SetSizer(sizer)
        self.select_kernel(self._kernelChoice.GetStringSelection())
        
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self._cancel)
        self.Bind(wx.EVT_BUTTON, self.on_plot_kernel, self._plot)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self._ok)
        self.Bind(wx.EVT_CHOICE, self.on_select_kernel, self._kernelChoice)
        #self.Bind(wx.EVT_CLOSE, self.on_close)
        
        self.plot()
                        
    @property
    def value(self):
        
        return self._value
                
    def on_cancel(self, event):
    
        self._value = None
    
        self.Close()
        
    def on_ok(self, event):
        
        if not self._parametersPanel.validate():
            return
        
        self._value = (self._currentKernel, self._parametersPanel.get_value())
        
        self.Close()
        
    def on_plot_kernel(self, event):
        
        self.plot()
        
    def plot(self):
        
        if not self._parametersPanel.validate():
            return
                            
        kernelClass = REGISTRY["instrument_resolution"][self._currentKernel]
        
        resolution = kernelClass()
        
        resolution.setup(self._parametersPanel.get_value())
        
        resolution.set_kernel(self._omegas, self._timeStep)
        
        self._axis.clear()
                                
        self._axis.plot(self._omegas, resolution.omegaWindow)
        self._axis.set_xlabel("omega (rad/ps)")
        self._axis.set_ylabel("instrument resolution (a.u)")

        self._canvas.draw()

    def on_select_kernel(self, event):
                                
        self.select_kernel(event.GetString())
        
        self.plot()
        
    def select_kernel(self, kernelName):
                
        if kernelName == self._currentKernel:
            return
        
        self._currentKernel = kernelName
        
        self._parametersSizer.Clear(deleteWindows=True)

        resolution = REGISTRY["instrument_resolution"][kernelName]()
        
        self.Freeze()
        
        self._parametersPanel = ConfigurationPanel(self, resolution,None)
        for w in self._parametersPanel.widgets.values():
            self.Bind(wx.EVT_TEXT_ENTER,self.plot,w.widget)
        
        self._parametersSizer.Add(self._parametersPanel, 0, wx.ALL|wx.EXPAND, 5)
                
        self.Thaw()
        
        self._parametersSizer.Layout()

        self.Fit()

class InstrumentResolutionWidget(IWidget):
        
    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._resolution = wx.TextCtrl(self._widgetPanel, wx.ID_ANY, value=str(self._configurator.default))

        self._setResolution = wx.Button(self._widgetPanel, wx.ID_ANY, label="Set")
        self._setResolution.Enable(False)
        
        sizer.Add(self._resolution, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self._setResolution, 0, wx.ALL|wx.EXPAND, 5)
        
        self.Bind(wx.EVT_BUTTON, self.on_set_instrument_resolution, self._setResolution)

        return sizer
        
    def get_widget_value(self):
        
        return eval(self._resolution.GetValue())

    def on_set_instrument_resolution(self, event):
                
        frameCfgName = self._configurator.dependencies["frames"]
        time = self.Parent.widgets[frameCfgName].time
        timeStep = time[1] - time[0]
        nSteps = len(time)
        
        self._instrumentResolutionDialog = InstrumentResolutionDialog(self, nSteps, timeStep)
        
        self._instrumentResolutionDialog.ShowModal()

        value = self._instrumentResolutionDialog.value
        
        if value is not None:
            self._resolution.SetValue(str(value))
        
        self._instrumentResolutionDialog.Destroy()

    def set_data(self, datakey):
                
        self._trajectory = DATA_CONTROLLER[datakey]
                        
        self._setResolution.Enable(True)
    
REGISTRY["instrument_resolution"] = InstrumentResolutionWidget
        
if __name__ == "__main__":
            
    app = wx.App(False)
    
    p = InstrumentResolutionDialog()
        
    p.SetSize((800,800))
            
    p.ShowModal()
    
    app.MainLoop()
                
