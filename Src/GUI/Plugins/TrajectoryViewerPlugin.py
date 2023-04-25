# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/AtomSelectionPlugin.py
# @brief     Implements module/class/test AtomSelectionPlugin
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from distutils.version import LooseVersion
import os

import wx
import wx.aui as wxaui

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg

from MMTK.Trajectory import TrajectoryVariable

from MDANSE import LOGGER, REGISTRY

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.Plugins.DataPlugin import get_data_plugin 
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin
                            
class TrajectoryViewerPlugin(ComponentPlugin):
        
    label = "Trajectory Viewer"
    
    ancestor = ["mmtk_trajectory", "molecular_viewer"]
    
    _dimensions = {'x':0, 'y':1, 'z':2}

    _units = {'configuration' : 'nm','velocities':'nm/ps','gradients':'amu*nm/ps2'}

    def __init__(self, parent, *args, **kwargs):

        ComponentPlugin.__init__(self,parent, size=(600,500), *args, **kwargs)

        PUBLISHER.subscribe(self.msg_select_atoms_from_viewer, 'msg_select_atoms_from_viewer')

    def build_panel(self):
                      
        panel = wx.Panel(self, wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        selectedOptionsSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        selectedVariableText = wx.StaticText(panel, wx.ID_ANY, label="Variable:")
        self._selectedVariable  = wx.ComboBox(panel, wx.ID_ANY, style=wx.CB_READONLY)

        selectedAtomText = wx.StaticText(panel, wx.ID_ANY, label="Atom:")
        self._selectedAtom  = wx.SpinCtrl(panel, wx.ID_ANY, style=wx.SP_WRAP|wx.SP_ARROW_KEYS)

        selectedDimensionText = wx.StaticText(panel, wx.ID_ANY, label="Dimension:")
        self._selectedDimension  = wx.ComboBox(panel, wx.ID_ANY, choices=['x','y','z'], style=wx.CB_READONLY)

        selectedOptionsSizer.Add(selectedVariableText,0,wx.LEFT|wx.ALIGN_CENTER_VERTICAL,2)
        selectedOptionsSizer.Add(self._selectedVariable,1,wx.CENTER|wx.EXPAND,2)
        selectedOptionsSizer.Add(selectedAtomText,0,wx.LEFT|wx.ALIGN_CENTER_VERTICAL,2)
        selectedOptionsSizer.Add(self._selectedAtom,1,wx.CENTER|wx.EXPAND,2)
        selectedOptionsSizer.Add(selectedDimensionText,0,wx.LEFT|wx.ALIGN_CENTER_VERTICAL,2)
        selectedOptionsSizer.Add(self._selectedDimension,1,wx.CENTER|wx.EXPAND,2)

        self._figure = Figure(figsize=(1,1))
        self._figure.add_subplot(111)
        self._canvas = FigureCanvasWxAgg(panel, wx.ID_ANY, self._figure)
        self._toolbar = NavigationToolbar2WxAgg(self._canvas)
        self._toolbar.Realize()

        self._selectedLine = None

        actionsSizer = wx.BoxSizer(wx.HORIZONTAL)

        clearPlotButton = wx.Button(panel,label='Clear')
        self._plotOnSameFigure = wx.CheckBox(panel,label='Plot on same figure')
        self._showLegend = wx.CheckBox(panel,label='Show legend')

        actionsSizer.Add(clearPlotButton,0,wx.CENTER,2)
        actionsSizer.Add(self._plotOnSameFigure,0,wx.CENTER,2)
        actionsSizer.Add(self._showLegend,0,wx.CENTER,2)

        sizer.Add(selectedOptionsSizer,0,wx.ALL|wx.EXPAND,2)
        sizer.Add(self._canvas, 1, wx.ALL|wx.EXPAND, 2)
        sizer.Add(self._toolbar)
        sizer.Add(actionsSizer,0,wx.ALIGN_CENTER,2)

        panel.SetSizer(sizer)
        sizer.Fit(panel)
        panel.Layout()

        self._mgr.AddPane(panel, wxaui.AuiPaneInfo().Center().Dock().CaptionVisible(False).CloseButton(False).MinSize(self.GetSize()))
        self._mgr.Update()

        self.Bind(wx.EVT_COMBOBOX,self.on_select_option,self._selectedVariable)
        self.Bind(wx.EVT_SPINCTRL,self.on_select_option, self._selectedAtom)
        self.Bind(wx.EVT_COMBOBOX,self.on_select_option, self._selectedDimension)
        self.Bind(wx.EVT_BUTTON,self.on_clear_plot, clearPlotButton)
        self.Bind(wx.EVT_CHECKBOX,self.on_showhide_legend, self._showLegend)

        self._canvas.mpl_connect("pick_event", self.on_pick_line)
        self._canvas.mpl_connect('key_press_event', self.on_key_press)

    def plug(self):
        
        self._parent._mgr.GetPane(self).Float().Floatable(True).Dockable(True).CloseButton(True)
        
        self._parent._mgr.Update()
        
        self.set_trajectory(self.dataproxy.data)
                                
    def set_trajectory(self,trajectory):

        self._trajectory = trajectory 
        universe = self._trajectory.universe
        nAtoms = universe.numberOfAtoms()

        self._target = os.path.basename(self._trajectory.filename)

        targetShape = (len(self._trajectory),nAtoms,3)

        trajectoryVariables = []
        for v in self._trajectory.variables():
            data = getattr(self._trajectory,v)
            if isinstance(data,TrajectoryVariable):
                if data.var.shape == targetShape:
                    trajectoryVariables.append(v)
        self._selectedVariable.SetItems(trajectoryVariables)

        self._selectedAtom.SetRange(0,nAtoms-1)
                                    
    def msg_select_atoms_from_viewer(self, message):

        dataPlugin,selection = message
        
        if dataPlugin != get_data_plugin(self):
            return

        self._selectedAtom.SetValue(selection[-1])

        self.on_select_option(None)

    def on_showhide_legend(self,event):

        if self._showLegend.GetValue():
            self._figure.gca().legend(loc='best')
        else:
            self._figure.gca().legend().remove()
        self._canvas.draw()

    def on_select_option(self, event):

        variable = self._selectedVariable.GetValue()
        atom = self._selectedAtom.GetValue()
        dimension = self._selectedDimension.GetValue()

        if not variable or not dimension:
            return

        atom = self._selectedAtom.GetValue()

        self._plot(variable,atom,dimension)

    def on_pick_line(self, event):
        # set alpha of previous selection to 1
        if self._selectedLine is not None:
            self._selectedLine.set_alpha(1.0)
            self._selectedLine.figure.canvas.draw()

        # unselect previous selection
        if event.artist == self._selectedLine:
            self._selectedLine = None
            return

        self._selectedLine = event.artist
        self._selectedLine.set_alpha(0.4)
        self._selectedLine.figure.canvas.draw()

    def on_key_press(self, event=None):
        if event.key == 'delete':
            if self._selectedLine is None:
                return

            d = wx.MessageDialog(None,'Do you really want delete this line ?','Question',wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            if d.ShowModal() == wx.ID_NO:
                return

            self._selectedLine.remove()
            self._selectedLine = None

            if not self._figure.gca().lines:
                self._figure.gca().set_prop_cycle(None)

            if self._showLegend.GetValue():
                self.update_legend()
                
            self._canvas.draw()

    def update_legend(self):

        self._figure.gca().legend().remove()
        if self._figure.gca().lines:        
            self._figure.gca().legend(loc='best')
        self._canvas.draw()

    def _plot(self, variable, atom, dimension):

        dimensionNumber = TrajectoryViewerPlugin._dimensions[self._selectedDimension.GetValue()]

        time = self._trajectory.time
        data = self._trajectory.readParticleTrajectory(atom,
                                                        0,
                                                        len(self._trajectory),
                                                        1,
                                                        variable=variable).array

        label = '%s - %d - %s' % (variable, atom, dimension)

        if not self._plotOnSameFigure.GetValue():
            self._figure.gca().clear()


        self._figure.gca().set_xlabel('time (ps)')
        self._figure.gca().set_ylabel('%s (%s)' % (variable,TrajectoryViewerPlugin._units.get(variable,'au')))
        self._figure.gca().plot(time,data[:,dimensionNumber],label=label,picker=3)
        self._canvas.draw()
        
        self.on_showhide_legend(None)

    def on_clear_plot(self,event):

        self._figure.gca().clear()
        self._canvas.draw()


REGISTRY["trajectory_viewer"] = TrajectoryViewerPlugin
        
