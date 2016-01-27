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

:author: Gael Goret, Bachir Aoun, Eric C. Pellegrini
'''

import collections

import numpy

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, NavigationToolbar2WxAgg
from matplotlib.figure import Figure
from matplotlib.colors import LogNorm, Normalize

import wx

from MDANSE.Core.Error import Error
from MDANSE.Externals.magnitude import magnitude

from MDANSE.Framework.Plugins.Plotter.Settings import ImageSettingsDialog
from MDANSE.Framework.Plugins.Plotter.Ticker import ScaledFormatter, ScaledLocator

NORMALIZER = {'log': LogNorm(), 'auto' : Normalize()}

class CrossSlicer(object):
    
    def __init__(self, parent, canvas, dialog, hplot, vplot, fig, color_index, hlegend, vlegend):
        self.related_plot = parent        
        self.canvas = canvas       
        self.dialog = dialog
        self.hplot = hplot
        self.vplot = vplot
        self.fig = fig
        self.color_index =color_index
        self.hlegend = hlegend
        self.vlegend = vlegend

class Plotter2DError(Error):
    pass   

class Plotter2D(wx.Panel):
    
    type = 'image'
    
    def __init__(self, parent, data = None):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self.setting = None
                
        ### Initialize variables ###
        self.parent = parent
        self.figure = Figure(figsize=(5,4), dpi=None)
        self.axes = self.figure.add_axes( (10,10,10,10), frameon=True, axisbg='b')
        self.canvas = FigureCanvasWxAgg( self, wx.ID_ANY, self.figure )
        self.toolbar = NavigationToolbar2WxAgg(self.canvas)
        self.ax = None
        self.color_bar = None
        self.slice_checkbox = wx.CheckBox(self, id=wx.ID_ANY, label="Slicing mode")
        
        self.annotation =  wx.StaticText(self, label='x : , y : , data[x,y] :' , style=wx.ALIGN_CENTER_VERTICAL)
        
        hsizer = wx.BoxSizer()
        hsizer.Add(self.toolbar, 0, flag=wx.ALL|wx.EXPAND)
        hsizer.Add(self.slice_checkbox, 0, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL )
        
        ### sizer ###
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, flag=wx.EXPAND) 
        self.sizer.Add(hsizer, 0, flag=wx.EXPAND)
        self.SetSizer(self.sizer) 
        
        ### set bindings ###
        self.Bind(wx.EVT_CHECKBOX, self.slice, id = self.slice_checkbox.GetId())
        
        # Slice attributes
        self.unique = False
        self.slice_event_id = None
        
        self.slice_coords = []
        self.slice_widget = []
                
        self.cross_slice_canvas = None 
        self.cross_slice_dialog = None
        self.h_cross_slice_plot = None
        self.v_cross_slice_plot = None
        self.cross_slice_fig = None
        self.cross_slice_color_index = -1
        self.h_cross_slice_legend = []
        self.v_cross_slice_legend = []
        self.color_list = collections.OrderedDict([['blue','b'],['green','g'],['red','r'],['cyan','c'],['magenta','m'],['yellow','y'],['black','k']])
        
        self.Xmin = 0
        self.Ymin = 0
        self.Xmax = 0
        self.Ymax = 0
        
        self.Xunit = None
        self.Yunit = None
        
        self.Xinit_unit = None
        self.Yinit_unit = None
        
        self.Xaxis =  [] 
        self.Yaxis =  []
        
        self.Xaxis_label = ''
        self.Yaxis_label = ''
        
        self.Xticks =  [] 
        self.Yticks =  []
        
        self.Xlabel = ''
        self.Ylabel = ''
        
        self.aspect = 'equal'
        self.interpolation = 'nearest'
        self.normType = 'none'
        
        hsizer = wx.BoxSizer()
        hsizer.Add(self.toolbar, 0, flag=wx.ALL|wx.EXPAND)
        hsizer.Add(self.slice_checkbox, 0, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL )
        hsizer.AddSpacer(25)
        hsizer.Add(self.annotation, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, flag=wx.EXPAND) 
        self.sizer.Add(hsizer, 0, flag=wx.EXPAND)
        self.SetSizer(self.sizer) 
        
        ### set bindings ###
        self.Bind(wx.EVT_CHECKBOX, self.slice, id = self.slice_checkbox.GetId())
        self.menu_event_id = self.canvas.mpl_connect('button_press_event', self.on_click)
        self.on_motion_id = self.canvas.mpl_connect('motion_notify_event', self.on_motion)
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
        
    def on_click(self, event = None):
        if event.button != 3:
            return
        
        popupMenu = wx.Menu()

        settings = popupMenu.Append(wx.ID_ANY, "Settings")
        popupMenu.Bind(wx.EVT_MENU, self.image_setting_dialog, settings)
        
        popupMenu.AppendSeparator()
        
        export = popupMenu.Append(wx.ID_ANY, "Export data")
        popupMenu.Bind(wx.EVT_MENU, self.export_data, export)

        self.canvas.ReleaseMouse()
        wx.CallAfter(self.PopupMenu, popupMenu) 
    
    def on_motion(self, event):
        if event.inaxes:
            x = event.xdata
            y = event.ydata
            if self.Xmin <= x and x <= self.Xmax and self.Ymin <= y and y <= self.Ymax:
                try:
                    dx = (self.Xmax - self.Xmin)/float(self.data.shape[1])
                    dy = (self.Ymax - self.Ymin)/float(self.data.shape[0])
                    X = numpy.floor((x - self.Xmin)/dx)
                    Y = numpy.floor((y - self.Ymin)/dy)
                    i = self.data[Y, X]
                    self.annotation.SetLabel('x : %g (%g), y : %g (%g), data[x,y] : %g'%(X,x*self.Xunit_conversion_factor,Y,y*self.Yunit_conversion_factor,i))
                except:
                    self.annotation.SetLabel('') # rarely useful except outside figure

        else:
            self.annotation.SetLabel('')
   
   
    def export_data(self, event = None):
        header = '# Data         : %s\n# First row    : %s (%s)\n# First column : %s (%s)\n' % (self.varname,self.Xlabel,self.Xunit,self.Ylabel,self.Yunit)
        output_fname = self.get_output_filename()
        
        x = numpy.concatenate(([0],self.Xaxis))*self.Xunit_conversion_factor
        data = numpy.vstack((x,numpy.hstack((self.Yaxis[:,numpy.newaxis]*self.Yunit_conversion_factor,self.data))))
        if output_fname:
            with open(output_fname, 'w') as f:
                f.write(header)
                numpy.savetxt(f, data, fmt='%12.4e', delimiter="  ")
                f.close()
    
    def get_output_filename(self):
        path = ''
        dlg = wx.FileDialog(self, "Save As", '', '', "All Files|*.*", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        return path
    
    def slice(self, event):
        if not event.IsChecked():
            self.canvas.mpl_disconnect(self.slice_event_id)
            self.slice_event_id = None
            self.menu_event_id = self.canvas.mpl_connect('button_press_event', self.on_click)
            self.canvas.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
            for w in self.slice_widget:
                w.remove()
            self.slice_widget = []
            
            self.cross_slice_fig = None
            self.segment_slice_fig = None
            
            self.segment_slice_color_index = 0 
            self.cross_slice_color_index = -1
            self.v_cross_slice_plot = None
            self.h_cross_slice_plot = None
            self.segment_slice_legend = []
            self.h_cross_slice_legend = []
            self.v_cross_slice_legend = []
            if self.cross_slice_dialog:
                self.cross_slice_dialog.Close()
            self.canvas.draw()
            return
        self.canvas.mpl_disconnect(self.menu_event_id)
        self.menu_event_id = None
        self.slice_event_id = self.canvas.mpl_connect('button_press_event', self.build_slice_widget) 
        self.canvas.SetCursor(wx.CROSS_CURSOR)
        self.canvas.draw() 

        
    def build_slice_widget(self, event):
        
        if not event.inaxes:
                return
                
        elif event.button == 1: # CROSS SLICING CASE
            
            x, y = event.xdata , event.ydata
            dx = (self.Xmax - self.Xmin)/float(self.data.shape[1])
            dy = (self.Ymax - self.Ymin)/float(self.data.shape[0])
            X = numpy.floor((x - self.Xmin)/dx)
            Y = numpy.floor((y - self.Ymin)/dy)
            vslice, hslice = self.extract_cross_slice(X, Y)
            
            if not self.parent.unique_slicer is None:
                self.cross_slice_dialog = self.parent.unique_slicer.dialog
                self.cross_slice_canvas = self.parent.unique_slicer.canvas 
                self.h_cross_slice_plot = self.parent.unique_slicer.hplot
                self.v_cross_slice_plot = self.parent.unique_slicer.vplot
                self.cross_slice_fig = self.parent.unique_slicer.fig
                self.cross_slice_color_index = self.parent.unique_slicer.color_index
                self.parent.unique_slicer.color_index += 1
                self.h_cross_slice_legend = self.parent.unique_slicer.hlegend
                self.v_cross_slice_legend = self.parent.unique_slicer.vlegend
                
            elif self.cross_slice_fig is None or not self.cross_slice_fig:
                    self.cross_slice_fig = Figure()
                    self.v_cross_slice_plot = self.cross_slice_fig.add_subplot(211)
                    self.h_cross_slice_plot = self.cross_slice_fig.add_subplot(212)
            
            if self.cross_slice_dialog is None or not self.cross_slice_dialog:
                self.cross_slice_dialog = wx.Frame(self, title="Cross slicing")  
                self.cross_slice_canvas = FigureCanvasWxAgg(self.cross_slice_dialog, wx.ID_ANY, self.cross_slice_fig)
                self.cross_slice_toolbar = NavigationToolbar2WxAgg(self.cross_slice_canvas)
                
                    
                self.unique_target_checkbox = wx.CheckBox(self.cross_slice_dialog, id=wx.ID_ANY, label="Single target plot")
                self.Bind(wx.EVT_CHECKBOX, self.made_unique_target, id = self.unique_target_checkbox.GetId())
                self.unique_target_checkbox.SetValue(self.unique)
                
                self.auto_scale_button = wx.Button(self.cross_slice_dialog, id=wx.ID_ANY, label="Auto-Scale")
                self.Bind(wx.EVT_BUTTON, self.auto_scale_cross_plot, self.auto_scale_button)
                
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(self.cross_slice_canvas, 1, flag=wx.EXPAND) 
                hsizer = wx.BoxSizer()
                hsizer.Add(self.cross_slice_toolbar, 0, flag=wx.EXPAND)
                hsizer.AddSpacer(10)
                hsizer.Add(self.auto_scale_button,0 ,flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL )
                hsizer.AddSpacer(10)
                hsizer.Add(self.unique_target_checkbox, 0, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL )
                
                sizer.Add(hsizer, 0, flag=wx.EXPAND) 
                
                self.cross_slice_dialog.SetSizer(sizer) 
                sizer.Fit(self.cross_slice_dialog)
            
            self.cross_slice_color_index += 1 
            
            self.slice_widget.append(self.subplot.axvline(x=x, linewidth=3, color='%s'%self.get_circular_color(self.cross_slice_color_index)))
            self.slice_widget.append(self.subplot.axhline(y=y, linewidth=3, color='%s'%self.get_circular_color(self.cross_slice_color_index)))
            
            v_tmp_plot = self.v_cross_slice_plot.plot(self.Xaxis*self.Xunit_conversion_factor, vslice, color='%s'%self.get_circular_color(self.cross_slice_color_index))
            h_tmp_plot = self.h_cross_slice_plot.plot(self.Yaxis*self.Yunit_conversion_factor, hslice, color='%s'%self.get_circular_color(self.cross_slice_color_index))
            
            self.v_cross_slice_legend.append([v_tmp_plot[0],'%s = %8.3f' % (self.Ylabel,y)])
            self.h_cross_slice_legend.append([h_tmp_plot[0],'%s = %8.3f' % (self.Xlabel,x)])
            
            self.v_cross_slice_plot.set_xlabel(self.Xlabel + self.fmt_Xunit)
            self.h_cross_slice_plot.set_xlabel(self.Ylabel + self.fmt_Yunit)
            
            self.v_cross_slice_plot.legend(tuple([e[0] for e in self.v_cross_slice_legend]), tuple([e[1] for e in self.v_cross_slice_legend]), loc = 'best', frameon = True, shadow = True)
            self.h_cross_slice_plot.legend(tuple([e[0] for e in self.h_cross_slice_legend]), tuple([e[1] for e in self.h_cross_slice_legend]), loc = 'best', frameon = True, shadow = True)
            
            if self.aspect == 'auto':
                self.subplot.set_aspect("auto","datalim")
                
            self.canvas.draw()
            self.cross_slice_dialog.Show()
            self.cross_slice_canvas.draw()
            

    def made_unique_target(self, event):
        self.parent.unique_slicer = CrossSlicer(self,
                                                self.cross_slice_canvas, 
                                                self.cross_slice_dialog, 
                                                self.h_cross_slice_plot, 
                                                self.v_cross_slice_plot, 
                                                self.cross_slice_fig, 
                                                self.cross_slice_color_index, 
                                                self.h_cross_slice_legend, 
                                                self.v_cross_slice_legend) 
        if self.unique:
            self.cross_slice_canvas = None
            self.cross_slice_fig = None
            self.h_cross_slice_plot = None 
            self.v_cross_slice_plot = None 
            self.cross_slice_color_index = 0
            self.h_cross_slice_legend = []
            self.v_cross_slice_legend = []
            for w in self.slice_widget:
                w.remove()
            self.slice_widget = []
            self.canvas.draw() 
            self.parent.unique_slicer = None
            self.cross_slice_dialog.Close()

        self.unique = not self.unique
        

    def auto_scale_cross_plot(self, event):
        
        norm = Normalize()
        
        for hl in self.h_cross_slice_plot.get_lines(): 
            d = hl.get_ydata()
            norm.autoscale(d)
            hl.set_ydata(norm(d))
          
        for vl in self.v_cross_slice_plot.get_lines(): 
            d = vl.get_ydata()
            norm.autoscale(d)
            vl.set_ydata(norm(d))
        
        
        self.v_cross_slice_plot.relim()
        self.h_cross_slice_plot.relim()
        self.v_cross_slice_plot.autoscale_view(True,True,True)
        self.h_cross_slice_plot.autoscale_view(True,True,True)

        self.cross_slice_canvas.draw()
            
    def get_circular_color(self, idx):
        circ_idx = idx%len(self.color_list)
        return self.color_list.values()[circ_idx]
                    
    def extract_cross_slice(self, x, y):
        x = int(x)
        y = int(y)
        hslice = self.data.T[x,:]
        vslice = self.data.T[:,y]
        return vslice, hslice
        
    def set_lim(self):
        
        self.Xmin, self.Xmax = self.Xaxis[0], self.Xaxis[-1]
        if self.Xmin == self.Xmax:
            self.Xmin -= 1.0e-9
            self.Xmax += 1.0e-9
        
        self.Ymin, self.Ymax = self.Yaxis[0], self.Yaxis[-1]
        if self.Ymin == self.Ymax:
            self.Ymin -= 1.0e-9
            self.Ymax += 1.0e-9
    
    def reset_axis(self):
                
        self.figure.gca().axis([self.Xmin, self.Xmax, self.Ymin, self.Ymax])
        self.canvas.draw()
    
    def plot(self, data, varname, Xaxis = None, Xunit = None, Yaxis = None, Yunit = None, transposition = True):
        if data is None:
            return
        
        if ((Xaxis is None) or (Xunit is None) or (Yaxis is None) or (Yunit is None)):
            self.set_axis_property(varname,data)
        else:
            self.Xaxis = Xaxis
            self.Xunit = Xunit
            self.Yaxis = Yaxis
            self.Yunit = Yunit
        
        if transposition:
            self.data = data.T
        else:
            self.data = data
            
        self.varname = varname
        
        self.subplot = self.figure.add_subplot( 111 )   
                
        self.ax = self.subplot.imshow(self.data, interpolation=self.interpolation, origin='lower')

        self.subplot.set_aspect('auto')
        self.aspect = 'auto'

        self.Xlabel = self.Xaxis_label
        self.Ylabel = self.Yaxis_label
        self.figure.gca().set_xlabel(self.Xlabel + self.fmt_Xunit )
        self.figure.gca().set_ylabel(self.Ylabel + self.fmt_Yunit )
         
        self.set_lim()
        self.set_ticks()
        self.reset_axis()
        
        self.color_bar = self.figure.colorbar(self.ax)
        
        self.canvas.draw()
    
    def replot(self, oldinstance):
        
        self.data = oldinstance.data
        self.Xaxis = oldinstance.Xaxis
        self.Xunit = oldinstance.Xunit
        self.Yaxis = oldinstance.Yaxis
        self.Yunit = oldinstance.Yunit
        self.varname = oldinstance.varname
        self.Xaxis_label = oldinstance.Xaxis_label
        self.Yaxis_label = oldinstance.Yaxis_label
        self.normType = oldinstance.normType
        self.aspect = oldinstance.aspect
        self.subplot = self.figure.add_subplot( 111 )   
        
        self.ax = self.subplot.imshow(self.data, interpolation=self.interpolation, origin='lower')

        self.subplot.set_aspect(self.aspect)

        self.Xlabel = self.Xaxis_label
        self.Ylabel = self.Yaxis_label
        self.figure.gca().set_xlabel(self.Xlabel + self.fmt_Xunit )
        self.figure.gca().set_ylabel(self.Ylabel + self.fmt_Yunit )
        
        self.set_ticks()
        self.reset_axis()
        
        self.color_bar = self.figure.colorbar(self.ax)
        
        self.scale(onReplot = True)
        
        self.canvas.draw()
        
    def scale(self, onReplot = False):
        
        if not NORMALIZER.has_key(self.normType):
            self.color_bar.set_clim(self.data.min(), self.data.max())
            self.ax.set_norm(None)
            return
        
        norm = NORMALIZER[self.normType]
        norm.autoscale(self.data)
        
        try :
            self.ax.set_norm(norm)
        except ValueError:
            raise Plotter2DError('Could not set normalization : difference between minimum and maximum values is to small')

        if onReplot: 
            normd = norm(self.data)
            self.color_bar.set_clim(normd.min(), normd.max())
            
             
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
        
        self.ax.set_extent([self.Xmin, self.Xmax, self.Ymin, self.Ymax])
        
    def set_axis_property(self, varname, data):
        oldXunit = self.Xinit_unit
        oldYunit = self.Yinit_unit

        try :
            self.Xaxis_label = self.dataproxy[varname]['axis'][0]
            self.Xunit = self.Xinit_unit = self.dataproxy[self.Xaxis_label]['units']
            self.Xaxis = self.dataproxy[self.Xaxis_label]['data']
        except:
            self.Xunit = self.Xinit_unit = 'au'
            self.Xaxis = numpy.arange(data.shape[0]) 
            
        try :
            self.Yaxis_label = self.dataproxy[varname]['axis'][1]
            self.Yunit = self.Yinit_unit = self.dataproxy[self.Yaxis_label]['units']
            self.Yaxis = self.dataproxy[self.Yaxis_label]['data']
        except:
            self.Yunit = self.Yinit_unit = 'au'
            self.Yaxis = numpy.arange(data.shape[1]) 
            
        if not oldXunit is None:
            if oldXunit != self.Xinit_unit:
                raise Plotter2DError('the x axis unit (%s) of data-set %r is inconsistent with the unit (%s) of the precedent data plotted '%(self.Xinit_unit, varname,  oldXunit))
        if not oldYunit is None:
            if oldYunit != self.Yinit_unit:
                raise Plotter2DError('the y axis unit (%s) of data-set %r is inconsistent with the unit (%s) of the precedent data plotted '%(self.Yinit_unit, varname,  oldYunit))

        if self.Yaxis.shape[0] != data.shape[1]:
            raise Plotter2DError('the y axis dimension is inconsistent with the shape of data ')
        if self.Xaxis.shape[0] != data.shape[0]:
            raise Plotter2DError('the x axis dimension is inconsistent with the shape of data ')
            
    def image_setting_dialog(self, event = None):
        
        d = ImageSettingsDialog(self)
        d.SetFocus()
        d.ShowModal()
        d.Destroy()    