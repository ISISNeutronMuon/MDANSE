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
Created on Apr 10, 2015

@author: Gael Goret, Bachir Aoun, Eric C. Pellegrini
'''

import os

import numpy

# The matplotlib imports.
import matplotlib
from matplotlib.ticker import AutoMinorLocator, MultipleLocator, NullLocator, AutoLocator
from matplotlib.widgets import Cursor
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm, Normalize, NoNorm

import wx

# The VTK imports.
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor 

from MDANSE.Core.Error import Error
from MDANSE.Externals.magnitude import magnitude

NORMALIZER = {'log': LogNorm(), 'auto' : Normalize()}

class Plotter1DError(Error):
    pass   

class Plotter1D(wx.Panel):

    type = 'line'
    
    def __init__(self, parent, data = None):
    
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self.setting = None
                
        ### Initialize variables ###
        self.parent = parent
        self.figure = Figure(figsize=(5,4), dpi=None)
        self.axes = self.figure.add_axes( (10,10,10,10), frameon=True, axisbg='b')
        self.canvas = FigureCanvasWxAgg( self, wx.ID_ANY, self.figure )
        self.toolbar = NavigationToolbar2WxAgg(self.canvas)
        self.plots = {}
        self.selectedLine = None
        
    
        self.annotation =  wx.StaticText(self, label='x : , y : ' , style=wx.ALIGN_CENTER_VERTICAL)

        ### Initialize figure parameters ###
        self.title = ''
        self.titleStyle = 0
        self.titleWeight = 0
        self.titleWidth = 4 # large
        
        self.xlabel = ''
        self.xlabelStyle = 0
        self.xlabelWeight = 0
        self.xlabelWidth = 3 # medium
        
        self.ylabel = ''
        self.ylabelStyle = 0
        self.ylabelWeight = 0
        self.ylabelWidth = 3 # medium
        
        self.gridStyle = 'None'
        self.gridWidth = 1
        self.gridColor = (1,0,0)
        
        self.Xscale = 'linear'
        self.Yscale = 'linear'
        
        self.xMinorTicks = False
        self.yMinorTicks = False
        
        self.Xposition = 'none'
        self.Yposition = 'none'

        self.Xlabel = ''
        self.Ylabel = ''
        
        self.Xaxis_label = ''
        self.Yaxis_label = ''
        
        self.Xunit = None
        self.Yunit = None
        
        self.Xinit_unit = None
        self.Yinit_unit = None
        
        self.Xaxis = numpy.array([])
        self.Yaxis = numpy.array([])
        
        self.Xticks = []
        self.Yticks = []
        
        self.Xmax = 0
        self.Ymax = 0
        self.Xmin = 0
        self.Ymin = 0
        
        self.offset = 0.0
        self.verticalCut = None
        
        self.show_legend = False
        self.legend_location = 'best'
        self.legend_frameon = True
        self.legend_shadow = True
        self.legend_fancybox = False

        # add sliders
        cutSizer = wx.BoxSizer(wx.HORIZONTAL)
        offsetSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.offset_label = wx.StaticText(self, label="Offset Value" , style=wx.ALIGN_CENTER_VERTICAL)
        self.yAxisSliderOffset = wx.Slider(self, wx.ID_ANY, size = (60,27), style = wx.SL_HORIZONTAL)
        self.offset_multiplier_label = wx.StaticText(self, label="Modulation" , style=wx.ALIGN_CENTER_VERTICAL)
        self.yAxisOffset = wx.TextCtrl(self, wx.ID_ANY, size = (60,27), style = wx.TE_PROCESS_ENTER )
        self.yAxisOffset.SetValue('0.0')
        self.autoFitAxesButton = wx.Button(self, label = "Fit axes range", size = (120,27))

        hsizer = wx.BoxSizer()
        hsizer.Add(self.toolbar, 0, flag=wx.ALL|wx.EXPAND)
        hsizer.AddSpacer(25)
        hsizer.Add(self.annotation, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        
        hsizer2 = wx.BoxSizer()
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.offset_label, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.yAxisOffset, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.offset_multiplier_label, 0, flag=wx.ALIGN_CENTER_VERTICAL )
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.yAxisSliderOffset, 1, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        hsizer2.AddSpacer(5)
        hsizer2.Add(self.autoFitAxesButton,0, flag = wx.ALIGN_CENTER_VERTICAL)
        
        ### sizer ###
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, flag=wx.EXPAND) 
        self.sizer.Add(hsizer, 0, flag=wx.EXPAND)
        self.sizer.Add(hsizer2, 0, flag=wx.EXPAND)
        self.SetSizer(self.sizer) 
        
        ### set bindings ###
        self.Bind(wx.EVT_CLOSE, self.on_close_figure) 
        self.Bind(wx.EVT_TEXT_ENTER, self.on_offset ,id = self.yAxisOffset.GetId())
        self.Bind(wx.EVT_SCROLL,self.on_offset ,id = self.yAxisSliderOffset.GetId())
        self.Bind(wx.EVT_BUTTON, self.on_auto_fit, id = self.autoFitAxesButton.GetId())
#         self.Bind(wx.EVT_CHECKBOX, self.slice, id = self.slice_checkbox.GetId())
        
        self.binds_mpl_events()

        #### sizer automatically fitting window size ####
        self.toolbar.Realize()
        self.SetSizeHints(600,500,1000,1000) # SetSizeHints(minW, minH, maxW, maxH)
        self.sizer.Fit(self)
        self.Show(True)
        
    @property
    def dataproxy(self):
        return self.parent.dataproxy
    
    @property
    def fmt_Xunit(self):
        if not self.Xunit:
            return ''
        else:    
            return ' (' + self.Xunit + ')'
    
    @property
    def fmt_Yunit(self):
        if not self.Yunit:
            return ''
        else:    
            return ' (' + self.Yunit + ')'
    
    def binds_mpl_events(self):
        self.menu_event_id = self.canvas.mpl_connect('button_press_event', self.on_click)
        self.pick_event_id = self.canvas.mpl_connect("pick_event", self.on_pick_line)
        self.key_event_id = self.canvas.mpl_connect('key_press_event', self.on_key)  
        self.on_motion_id = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        
    def on_click(self, event = None):
        if event.button != 3:
            return
        
        popupMenu = wx.Menu()

        general = popupMenu.Append(wx.ID_ANY, "General settings")
        popupMenu.Bind(wx.EVT_MENU, self.general_setting_dialog, general)
        
        axes = popupMenu.Append(wx.ID_ANY, "Axes settings")
        popupMenu.Bind(wx.EVT_MENU, self.axes_setting_dialog, axes)
        
        lines = popupMenu.Append(wx.ID_ANY, "Lines settings")
        popupMenu.Bind(wx.EVT_MENU, self.lines_setting_dialog, lines)

        popupMenu.AppendSeparator()

        clear = popupMenu.Append(wx.ID_ANY, "Clear")
        popupMenu.Bind(wx.EVT_MENU, self.clear, clear)

        popupMenu.AppendSeparator()        


        export = popupMenu.Append(wx.ID_ANY, "Export data")
        popupMenu.Bind(wx.EVT_MENU, self.export_data, export)
        
        self.canvas.ReleaseMouse()
        wx.CallAfter(self.PopupMenu, popupMenu) 
    
    def on_motion(self, event):
        if event.inaxes:
            x = event.xdata
            y = event.ydata
            self.annotation.SetLabel('x : %g, y : %g'%(x,y))
        else:
            self.annotation.SetLabel('')
            
    def clear(self, event = None):
        d = wx.MessageDialog(None,
                 'Do you really want clean the plot window ?',
                 'Question',
                 wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            pass
        else:
            return
        self.plots = {}
        self.figure.gca().clear()
        self.figure.canvas.draw()  
           
    def on_offset(self, event = None):
        try :
            offsetValue = float(self.yAxisOffset.GetValue())
        except:
            offsetValue = 0.
        offsetPercent = float(self.yAxisSliderOffset.GetValue())/100.0
        AddFactor = float(offsetValue*offsetPercent) - float(self.offset)
        self.offset = float(offsetValue*offsetPercent) 
        
        self.add_offset(AddFactor)
    
    def export_data(self, event = None):

        first = True
        
        for v in self.plots.values():
           
            line, label, varname = v
            if first:
                try:
                    axis = self.dataproxy[varname]['axis'][0]
                    data = [self.dataproxy[axis]['data']]
                    labels = ['%s (%s)'%(axis, self.dataproxy[axis]['units'])]
                except:
                    data = [numpy.arange(self.dataproxy[varname]['data'].shape[0])]
                    labels = ['default_axis (au)']
                first = False
                    
            try:
                line.get_xydata()
                data.append(line.get_ydata())
                labels.append('%s (%s)'%(label, self.dataproxy[varname]['units']))
            except:
                raise Plotter1DError('encounter issue for variable %r while exporting data' % varname)
        header = '# '
        if labels:
            for l in labels:
                header += '%s, '%l
            header = header[:-2] + os.linesep   
        output_fname = self.get_output_filename()
        if output_fname:
            with open(output_fname, 'w') as f:
                f.write(header)
                numpy.savetxt(f,numpy.column_stack(data), fmt='%12.4e', delimiter="  ")
                f.close()
        
    def get_output_filename(self):
        path = ''
        dlg = wx.FileDialog(self, "Save As", '', '', "All Files|*.*", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        return path
            
    def add_offset(self, offset):
        lines = self.figure.gca().lines
        # remove vertical line if existing
        if self.verticalCut is not None :        
            lines.remove(self.verticalCut)
            self.verticalCut = None
            
        for idx in range(len(lines)):
            line = lines[idx]
            
            y = line.get_ydata()
            line.set_ydata( (idx+1)*offset +y  )
        
        # set activeFigure to this figure
        self.figure.canvas.draw()

    def on_auto_fit(self, event = None):
        lines = self.figure.gca().lines
        if lines == []:
            return
        xMin = 1.0e10
        xMax = 0
        yMin = 1.0e10
        yMax = 0
        for line in lines:
            xMin = min( xMin, min(line.get_xdata()) )
            xMax = max( xMax, max(line.get_xdata()) )
            yMin = min( yMin, min(line.get_ydata()) )
            yMax = max( yMax, max(line.get_ydata()) )
   
        self.Xmin =xMin
        self.Xmax = xMax
        self.Ymin = yMin
        self.Ymax=  yMax + 0.05*(yMax-yMin)
        
        self.figure.gca().axis([self.Xmin, self.Xmax, self.Ymin, self.Ymax])
        self.figure.canvas.draw()
    
    def on_key(self, event = None):
        if event.key =='delete':
            if self.selectedLine is None:
                return
            # remove offset
            self.add_offset(-self.offset)
            # actualize plotsFileData
            for k,v in self.plots.items():
                if v[0] is self.selectedLine:
                    d = wx.MessageDialog(None,
                             'Do you really want delete this line ?',
                             'Question',
                             wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
                    if d.ShowModal() == wx.ID_YES:
                        pass
                    else:
                        return
                    self.plots.pop(k)
            # remove line
            self.selectedLine.remove()
            # add offset
            self.add_offset(self.offset)
            self.update_legend()
            self.selectedLine = None
            self.canvas.draw()
    
    def delete_line(self, line): 
        self.add_offset(-self.offset)
        
        for k,v in self.plots.items():
            if v[0] is line: 
                self.plots.pop(k)
        
        line.remove()
        self.add_offset(self.offset)
        self.canvas.draw()
        
    def on_close_figure(self, event = None):
        # remove any selection made in any figure
        if self.parent.selectedPlot is not None:
            self.parent.selectedPlot = None
        
        # destroy window
        self.Destroy()
        self = None

    def scale_xAxis(self):
        scaleStr = self.Xscale
        if scaleStr == 'linear':
            self.figure.gca().set_xscale('linear')
        elif  scaleStr == 'symlog':
            self.figure.gca().set_xscale('symlog')
        elif scaleStr == 'ln':
            self.figure.gca().set_xscale('log', basex=numpy.exp(1))
        elif scaleStr == 'log 10':
            self.figure.gca().set_xscale('log', basex=10)
        elif scaleStr == 'log 2':
            self.figure.gca().set_xscale('log', basex=2)
        self.on_auto_fit()  
        self.figure.canvas.draw()
        
    def scale_yAxis(self):
        scaleStr = self.Yscale
        if scaleStr == 'linear':
            self.figure.gca().set_yscale('linear')
        elif  scaleStr == 'symlog':
            self.figure.gca().set_yscale('symlog')
        elif scaleStr == 'ln':
            self.figure.gca().set_yscale('log', basex=numpy.exp(1))
        elif scaleStr == 'log 10':
            self.figure.gca().set_yscale('log', basex=10)
        elif scaleStr == 'log 2':
            self.figure.gca().set_yscale('log', basex=2)
        self.on_auto_fit() 
        self.figure.canvas.draw()
        
    def on_pick_line(self, event = None):
        # set alpha of previous selection to 1
        if self.selectedLine is not None: 
            self.selectedLine.set_alpha(1.0)
            self.selectedLine.figure.canvas.draw()
        # unselect previous selection
        if event.artist == self.selectedLine:
            self.selectedLine = None
            return 
        # set new selection and alpha  
        self.selectedLine = event.artist
        self.selectedLine.set_alpha(0.4)
        self.selectedLine.figure.canvas.draw()

    def update_legend(self):
        legend = [[],[]] 
        for v in self.plots.values():
            legend[0].append(v[0])
            legend[1].append(v[1]) 
        self.figure.gca().legend(tuple(legend[0]), tuple(legend[1]), loc = self.legend_location, frameon = self.legend_frameon, shadow = self.legend_shadow, fancybox = self.legend_fancybox) 
        self.show_legend = True
        
    def Plot(self, data, varname):
        if data is None:
            return
        self.set_axis_property(varname, data)
        self.subplot = self.figure.add_subplot( 111 )  
        name = self.unique(varname, self.plots) 
        self.plots[name] = [self.subplot.plot(self.Xaxis, data, picker = 3)[0], name, varname]
        self.set_ticks()
        self.Xlabel = self.Xaxis_label
        self.Ylabel = self.Yaxis_label
        self.figure.gca().set_xlabel(self.Xlabel + self.fmt_Xunit )
        self.figure.gca().set_ylabel(self.Ylabel + self.fmt_Yunit )
        self.on_auto_fit()
        self.canvas.draw() 
    
    def set_axis_property(self, varname, data):
        oldXunit = self.Xinit_unit
        oldYunit = self.Yinit_unit
        self.Yaxis_label = varname
        self.Yaxis = self.dataproxy[varname]['data']
        try :
            self.Xaxis_label = self.dataproxy[varname]['axis'][0]
            self.Xunit = self.Xinit_unit = self.dataproxy[self.Xaxis_label]['units']
            self.Xaxis = self.dataproxy[self.Xaxis_label]['data']
        except:
            self.Xunit = self.Xinit_unit = 'au'
            self.Xaxis = numpy.arange(data.shape[0]) 
        try :
            self.Yunit = self.Yinit_unit = self.dataproxy[varname]['units']
        except:
            self.Yunit = self.Yinit_unit = 'au'
            
        
        
        if not oldXunit is None:
            if oldXunit != self.Xinit_unit:
                raise Plotter1DError('the x axis unit (%s) of data-set %r is inconsistent with the unit (%s) of the precedent data plotted '%(self.Xinit_unit, varname,  oldXunit))
        if not oldYunit is None:
            if oldYunit != self.Yinit_unit:
                raise Plotter1DError('the y axis unit (%s) of data-set %r is inconsistent with the unit (%s) of the precedent data plotted '%(self.Yinit_unit, varname,  oldYunit))
    
    def compute_conversion_factor(self):
        try:
            self.Xunit_conversion_factor = magnitude.mg(1., self.Xinit_unit, self.Xunit).toval()
        except magnitude.MagnitudeError:
            self.Xunit_conversion_factor = 1.0
        
        try:
            self.Yunit_conversion_factor = magnitude.mg(1., self.Yinit_unit, self.Yunit).toval()
        except magnitude.MagnitudeError:
            self.Yunit_conversion_factor = 1.0
                   
    def set_ticks(self):
        self.compute_conversion_factor()
        
        self.figure.gca().xaxis.set_major_locator(ScaledLocator(dx = self.Xunit_conversion_factor))
        self.figure.gca().xaxis.set_major_formatter(ScaledFormatter(dx = self.Xunit_conversion_factor))      
        
        self.figure.gca().yaxis.set_major_locator(ScaledLocator(dx = self.Yunit_conversion_factor))
        self.figure.gca().yaxis.set_major_formatter(ScaledFormatter(dx = self.Yunit_conversion_factor)) 
                                                    
    def unique(self, key, dict):
        skey = key
        i = 0
        while dict.has_key(key):
            key = skey + '_%d'%i
            i += 1
        return key 
    
    def general_setting_dialog(self, event = None):
        d = GeneralSettingsDialog(self)
        d.SetFocus()
        d.ShowModal()
        d.Destroy()
        
    def axes_setting_dialog(self, event = None):
        d = AxesSettingsDialog(self)
        d.SetFocus()
        d.ShowModal()
        d.Destroy()
        
    def lines_setting_dialog(self, event = None):
        d = LinesSettingsDialog(self)
        d.SetFocus()
        d.ShowModal()
        d.Destroy()    