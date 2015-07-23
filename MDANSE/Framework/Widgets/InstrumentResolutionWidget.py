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

import numpy

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import wx

from MDANSE import REGISTRY
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.Widgets.IWidget import IWidget
from MDANSE.GUI import DATA_CONTROLLER
from MDANSE.GUI.ComboWidgets.ConfigurationPanel import ConfigurationPanel

class InstrumentResolutionDialog(wx.Dialog):
    
    def __init__(self, parent=None, nSteps=100, timeStep=1.0):
        
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Instrument resolution", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)

        self._parent = parent
    
        self._nSteps = nSteps
        
        self._timeStep = timeStep
        
        self._frequencies = numpy.fft.fftshift(numpy.fft.fftfreq(self._nSteps, self._timeStep))
                
        self._currentKernel = None
                          
        self._value = None
                                
        self.build_dialog()
        
    def build_dialog(self):

        sizer = wx.GridBagSizer(5,5)
        
        sb = wx.StaticBox(self, wx.ID_ANY, label="kernel")
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        self._kernelChoice = wx.Choice(self, wx.ID_ANY, choices=REGISTRY["instrument_resolution"].keys())
        self._kernelChoice.SetSelection(0)
        sbSizer.Add(self._kernelChoice, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(sbSizer, (0,0), flag=wx.EXPAND)

        self._parametersWidgets = ['',{}]
        sb = wx.StaticBox(self, wx.ID_ANY, label="parameters")
        self._parametersSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)        
        sizer.Add(self._parametersSizer, (1,0), flag=wx.EXPAND)

        sb = wx.StaticBox(self, wx.ID_ANY)
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        self._cancel = wx.Button(self, wx.ID_ANY, label="Cancel")
        self._plot = wx.Button(self, wx.ID_ANY, label="Plot")
        self._ok = wx.Button(self, wx.ID_ANY, label="OK")
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
        self.Bind(wx.EVT_CLOSE, self.on_cancel)
                
    @property
    def value(self):
        
        return self._value
                
    def on_cancel(self, event):
        
        self._value = None
                                
        self.Destroy()
        
    def on_ok(self, event):
        
        if not self._parametersPanel.validate():
            return
        
        self._value = (self._currentKernel, self._parametersPanel.get_value())
        
        self.Destroy()
        
    def on_plot_kernel(self, event):
        
        if not self._parametersPanel.validate():
            return
                            
        kernelClass = REGISTRY["instrument_resolution"][self._currentKernel]
        
        resolution = kernelClass()
        
        resolution.setup(self._parametersPanel.get_value())
        
        resolution.set_kernel(self._frequencies, self._timeStep)
        
        self._axis.clear()
                        
        self._axis.plot(self._frequencies, resolution.frequencyWindow)
        self._axis.set_xlabel("frequency (THz)")
        self._axis.set_ylabel("instrument resolution (a.u)")

        self._canvas.draw()

    def on_select_kernel(self, event):
                        
        self.select_kernel(event.GetString())
        
    def select_kernel(self, kernelName):
                
        if kernelName == self._currentKernel:
            return
        
        self._currentKernel = kernelName
        
        self._parametersSizer.Clear(deleteWindows=True)

        resolution = REGISTRY["instrument_resolution"][kernelName]()
        
        self.Freeze()
        
        self._parametersPanel = ConfigurationPanel(self, resolution)
        
        self._parametersSizer.Add(self._parametersPanel, 0, wx.ALL|wx.EXPAND, 5)
                
        self.Thaw()
        
        self._parametersSizer.Layout()

        self.Fit()

class InstrumentResolutionConfigurator(IWidget):
    
    type = "instrument_resolution"
    
    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._resolution = wx.TextCtrl(self._widgetPanel, wx.ID_ANY, value=str(self._configurator.default))

        self._setResolution = wx.Button(self._widgetPanel, wx.ID_ANY, label="Set")
        self._setResolution.Enable(False)
        
        sizer.Add(self._resolution, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self._setResolution, 0, wx.ALL|wx.EXPAND, 5)
        
        self.Bind(wx.EVT_BUTTON, self.on_set_instrument_resolution, self._setResolution)

        pub.subscribe(self.set_data, ("msg_set_netcdf"))

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