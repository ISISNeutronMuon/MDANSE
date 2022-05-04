# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/PlotterSettings.py
# @brief     Implements module/class/test PlotterSettings
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import matplotlib

import wx
from MDANSE.Core.Error import Error
from MDANSE.Framework.Units import UnitError, measure

class UnitsSettingsError(Error):
    pass

class UnitsSettingsDialog():
    def checkUnits(self, oldUnit, newUnit):
        if oldUnit != newUnit:
            try:
                m = measure(1.0,oldUnit,equivalent=True)
                m.toval(newUnit)
            except UnitError:
                raise UnitsSettingsError("the axis unit (%s) is inconsistent with the current unit (%s) "%(newUnit, oldUnit))

class ImageSettingsDialog(wx.Dialog, UnitsSettingsDialog):
    
    def __init__(self, parent=None):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Image Settings", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.build_dialog()
        
    def build_dialog(self):
        
        self.norm_choices = ['none', 'log']
        self.aspect_choices = ['equal', 'auto']
        self.interpolation_choices =  ['none', 'nearest', 'bilinear', 'bicubic', 'spline16', \
                                       'spline36', 'hanning', 'hamming', 'hermite', 'kaiser', \
                                        'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', \
                                         'sinc', 'lanczos']
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        
        sb = wx.StaticBox(self, wx.ID_ANY, label = "Label")
        sbsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        gbSizer = wx.GridBagSizer(5,5)
        
        self.title_label = wx.StaticText(self, label="Title" , style=wx.ALIGN_CENTER_VERTICAL)
        self.title = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Xlabel_label = wx.StaticText(self, label="X Axis", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xlabel = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Ylabel_label = wx.StaticText(self, label="Y Axis", style=wx.ALIGN_CENTER_VERTICAL)
        self.Ylabel = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        gbSizer.Add(self.title_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.title, (0,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer.Add(self.Xlabel_label, (1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.Xlabel, (1,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer.Add(self.Ylabel_label, (2,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self.Ylabel, (2,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        gbSizer.AddGrowableCol(1)
        
        sbsizer.Add(gbSizer, 0, wx.EXPAND, 5)
        
        Sizer.Add(sbsizer, 0, wx.EXPAND)
        

        gbSizer2 = wx.GridBagSizer(5,5)
        
        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        
        sb2 = wx.StaticBox(self, wx.ID_ANY, label = "Aspect")
        sbsizer2 = wx.StaticBoxSizer(sb2, wx.VERTICAL)
        
        self.aspect_label = wx.StaticText(self, label="Proportions" , style=wx.ALIGN_CENTER_VERTICAL)
        self.aspect = wx.ComboBox(self, id = wx.ID_ANY, choices=self.aspect_choices, style=wx.CB_READONLY)
        
        self.interpolation_label = wx.StaticText(self, label="Interpolation" , style=wx.ALIGN_CENTER_VERTICAL)
        self.interpolation = wx.ComboBox(self, id = wx.ID_ANY, choices=self.interpolation_choices, style=wx.CB_READONLY)
        
        self.norm_label = wx.StaticText(self, label="Scale" , style=wx.ALIGN_CENTER_VERTICAL)
        self.normType = wx.ComboBox(self, id = wx.ID_ANY, choices=self.norm_choices, style=wx.CB_READONLY)
        self.normType.SetValue(self.norm_choices[0])
        
        gbSizer2.Add(self.aspect_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer2.Add(self.aspect, (0,2), flag = wx.ALIGN_CENTER_VERTICAL)
       
        gbSizer2.Add(self.interpolation_label,(1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer2.Add(self.interpolation, (1,2), flag = wx.ALIGN_CENTER_VERTICAL)     
        
        gbSizer2.Add(self.norm_label,(2,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer2.Add(self.normType, (2,2), flag = wx.ALIGN_CENTER_VERTICAL)         
                
        sbsizer2.Add(gbSizer2, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        gbSizer1 = wx.GridBagSizer(5,5)
        
        sb1 = wx.StaticBox(self, wx.ID_ANY, label = "Units")
        sbsizer1 = wx.StaticBoxSizer(sb1, wx.VERTICAL)
        
        self.X_label = wx.StaticText(self, label="X", style=wx.ALIGN_CENTER_VERTICAL)

        self.Xunit = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        self.Y_label = wx.StaticText(self, label="Y", style=wx.ALIGN_CENTER_VERTICAL)

        self.Yunit = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        gbSizer1.Add(self.X_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Xunit, (0,2), flag = wx.ALIGN_CENTER_VERTICAL)
       
        gbSizer1.Add(self.Y_label,(1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Yunit, (1,2), flag = wx.ALIGN_CENTER_VERTICAL)
        
        sbsizer1.Add(gbSizer1, 0, wx.EXPAND, 5)
        
        hsizer.Add(sbsizer2,0,wx.EXPAND)
        hsizer.Add(sbsizer1,0,wx.EXPAND)
        
        Sizer.Add(hsizer, 0, wx.EXPAND)
        
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button  = wx.Button(self, wx.ID_ANY, label="Apply")
        hsizer1.Add(self.apply_button, 0, wx.EXPAND, 0)
        
        Sizer.Add(hsizer1, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.ALL, 5)
        
        self.SetSizer(Sizer)        
        Sizer.Fit(self)
        self.Layout()
        
        self.Bind(wx.EVT_BUTTON, self.set_settings, self.apply_button)
        
        self.get_settings()
    
    def get_settings(self, event = None):
        self.title.SetValue(self.parent.figure.gca().get_title())
        self.Xlabel.SetValue(self.parent.Xlabel)
        self.Ylabel.SetValue(self.parent.Ylabel)
        
        self.Xunit.SetValue(str(self.parent.Xunit))
        self.Yunit.SetValue(str(self.parent.Yunit))
        
        self.aspect.SetValue(self.parent.figure.gca().get_aspect())
        self.interpolation.SetValue(self.parent.interpolation)
        self.normType.SetValue(self.parent.normType)
        
    def set_settings(self, event = None):
        self.checkUnits(self.parent.Xunit, self.Xunit.GetValue())
        self.checkUnits(self.parent.Yunit, self.Yunit.GetValue())
          
        self.parent.figure.gca().set_title(self.title.GetValue())
        self.parent.Xlabel = self.Xlabel.GetValue()
        self.parent.Ylabel = self.Ylabel.GetValue()
        
        if self.parent.Xunit !=self.Xunit.GetValue() or self.parent.Yunit != self.Yunit.GetValue():
            self.parent.Xunit = self.Xunit.GetValue()
            self.parent.Yunit = self.Yunit.GetValue()
            self.parent.set_ticks()
            self.parent.reset_axis()
         
        self.parent.figure.gca().set_xlabel(self.parent.Xlabel + self.parent.fmt_Xunit )
        self.parent.figure.gca().set_ylabel(self.parent.Ylabel + self.parent.fmt_Yunit )
         
        self.parent.aspect = self.aspect.GetValue()
        self.parent.interpolation = self.interpolation.GetValue()
        self.parent.normType = self.normType.GetValue()
        
        self.parent.figure.gca().set_aspect(self.parent.aspect)
        self.parent.ax.set_interpolation(self.parent.interpolation)
        
        self.parent.scale(True)
        self.parent.color_bar.update_normal(self.parent.ax)
        self.parent.canvas.draw()
    

class GeneralSettingsDialog(wx.Dialog):
    
    def __init__(self, parent=None):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="General Settings", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.build_dialog()
        
    def build_dialog(self):
        self.legend_location_choice = ['best' , 'upper right' , 'upper left' ,\
                                     'lower left' , 'lower right' , 'right' ,\
                                     'center left','center right','lower center',\
                                     'upper center','center']
        self.style_choice = ['-' , '--' , '-.' , ':', 'None']
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        sb = wx.StaticBox(self, wx.ID_ANY, label = "Label")
        sbsizer0 = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        gbSizer0 = wx.GridBagSizer(5,5)
        
        self.title_label = wx.StaticText(self, label="Title" , style=wx.ALIGN_CENTER_VERTICAL)
        self.title = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Xlabel_label = wx.StaticText(self, label="X Axis", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xlabel = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Ylabel_label = wx.StaticText(self, label="Y Axis", style=wx.ALIGN_CENTER_VERTICAL)
        self.Ylabel = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        gbSizer0.Add(self.title_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.title, (0,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer0.Add(self.Xlabel_label, (1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Xlabel, (1,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        gbSizer0.Add(self.Ylabel_label, (2,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ylabel, (2,1), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        gbSizer0.AddGrowableCol(1)
        
        sbsizer0.Add(gbSizer0, 1, wx.EXPAND, 5)
        
        sb = wx.StaticBox(self, wx.ID_ANY, label = "Legend")
        sbsizer1 = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        self.show_legend = wx.CheckBox(self, id=wx.ID_ANY, label="Show")
        
        hsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.legend_location_label = wx.StaticText(self, label="Location" , style=wx.ALIGN_CENTER_VERTICAL)
        self.legend_location = wx.ComboBox(self, id = wx.ID_ANY, choices=self.legend_location_choice, style=wx.CB_READONLY)
        self.legend_location.SetValue(self.legend_location_choice[0])
        self.legend_style_label = wx.StaticText(self, label="Style" , style=wx.ALIGN_CENTER_VERTICAL)
        self.frame_on = wx.CheckBox(self, id=wx.ID_ANY, label="Frame on")
        self.fancy_box = wx.CheckBox(self, id=wx.ID_ANY, label="Fancy box")
        self.shadow = wx.CheckBox(self, id=wx.ID_ANY, label="Shadow")
        
        self.frame_on.SetValue(True)
        self.fancy_box.SetValue(False)
        self.shadow.SetValue(True)
        
        hsizer3.Add(self.legend_location_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.Add(self.legend_location, 1,wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.AddSpacer(20)
        hsizer3.Add(self.legend_style_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.Add(self.frame_on, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.Add(self.fancy_box, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer3.Add(self.shadow, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        sbsizer1.Add(self.show_legend, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sbsizer1.Add(hsizer3, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        sb = wx.StaticBox(self, wx.ID_ANY, label = "Grid")
        sbsizer2 = wx.StaticBoxSizer(sb, wx.VERTICAL)
        
        hsizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.grid_syle_label = wx.StaticText(self, label="Style" , style=wx.ALIGN_CENTER_VERTICAL)
        self.grid_style = wx.ComboBox(self, id = wx.ID_ANY, choices=self.style_choice, style=wx.CB_READONLY)
        
        self.grid_style.SetValue(self.style_choice[-1])
        
        self.grid_width_label = wx.StaticText(self, label="Width" , style=wx.ALIGN_CENTER_VERTICAL)
        self.grid_width = wx.SpinCtrl(self, id=wx.ID_ANY, style = wx.SP_ARROW_KEYS)
        
        self.grid_color_label = wx.StaticText(self, label="Color" , style=wx.ALIGN_CENTER_VERTICAL)
        self.grid_color_picker = wx.ColourPickerCtrl(self, id = wx.ID_ANY, col = 'black')
        
        hsizer4.Add(self.grid_syle_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.Add(self.grid_style, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.AddSpacer(20)
        hsizer4.Add(self.grid_width_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.Add(self.grid_width, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.AddSpacer(20)
        hsizer4.Add(self.grid_color_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        hsizer4.Add(self.grid_color_picker, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        
        sbsizer2.Add(hsizer4, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        hsizer5 = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button  = wx.Button(self, wx.ID_ANY, label="Apply")
        hsizer5.Add(self.apply_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALIGN_RIGHT, 0)
        
        Sizer.Add(sbsizer0, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        Sizer.Add(sbsizer1, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        Sizer.Add(sbsizer2, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        Sizer.Add(hsizer5, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.ALL, 5)
        
        self.SetSizer(Sizer)        
        Sizer.Fit(self)
        self.Layout()    

        self.Bind(wx.EVT_BUTTON, self.set_settings, self.apply_button)
        
        self.get_settings()
    
    def get_settings(self, event = None):
        self.title.SetValue(self.parent.figure.gca().get_title())
        self.Xlabel.SetValue(self.parent.Xlabel)
        self.Ylabel.SetValue(self.parent.Ylabel)
        self.show_legend.SetValue(self.parent.show_legend)
        self.grid_style.SetValue(self.parent.gridStyle)
        self.grid_width.SetValue(self.parent.gridWidth)
        self.grid_color_picker.SetColour(wx.Colour(int(self.parent.gridColor[0]*255),int(self.parent.gridColor[1]*255),int(self.parent.gridColor[2]*255)))
        
    def set_settings(self, event = None):
        
        self.parent.figure.gca().set_title(self.title.GetValue())
        self.parent.Xlabel = self.Xlabel.GetValue()
        self.parent.Ylabel = self.Ylabel.GetValue()
        
        self.parent.figure.gca().set_xlabel(self.parent.Xlabel +  self.parent.fmt_Xunit)
        self.parent.figure.gca().set_ylabel(self.parent.Ylabel +  self.parent.fmt_Yunit)
        
        if self.show_legend.GetValue():
            self.parent.show_legend = True
            self.update_currentFig_legend()
        else:
            self.parent.show_legend = False
            self.parent.figure.gca().legend_ = None
        
        self.update_currentFig_grid()
        
        self.parent.canvas.draw()  
        
    def update_currentFig_legend(self):
        self.parent.legend_location = self.legend_location.GetValue()
        self.parent.legend_frameon = self.frame_on.GetValue()
        self.parent.legend_shadow = self.shadow.GetValue()
        self.parent.legend_fancybox = self.fancy_box.GetValue()

        self.parent.update_legend()  
  
        self.parent.canvas.draw()
    
    def update_currentFig_grid(self):
        style = self.grid_style.GetValue()
        width = self.grid_width.GetValue()
        color = self.grid_color_picker.GetColour()
        rvb_color = (color.Red()/255., color.Green()/255., color.Blue()/255.)

        self.parent.gridStyle = style
        self.parent.gridWidth = width
        self.parent.gridColor = rvb_color
        
        self.parent.figure.gca().grid(True, linestyle = style)
        self.parent.figure.gca().grid(True, linewidth = width)
        self.parent.figure.gca().grid(True, color = rvb_color)
        
        self.parent.canvas.draw() 
                

class AxesSettingsDialog(wx.Dialog, UnitsSettingsDialog):
    
    def __init__(self, parent=None):
        
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Axes Settings", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.build_dialog()
        
    def build_dialog(self):
        
        self.axis_scales_choices = ['linear', 'symlog', 'ln', 'log 10', 'log 2']
              
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        hsizer0 = wx.BoxSizer(wx.HORIZONTAL)
        
        sb0 = wx.StaticBox(self, wx.ID_ANY, label = "Bounds")
        sbsizer0 = wx.StaticBoxSizer(sb0, wx.VERTICAL)
        
        gbSizer0 = wx.GridBagSizer(5,5)
        
        self.Xmin_label = wx.StaticText(self, label="X Min", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xmin = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Ymin_label = wx.StaticText(self, label="Y Min", style=wx.ALIGN_CENTER_VERTICAL)
        self.Ymin = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        self.Xmax_label = wx.StaticText(self, label="X Max", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xmax = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.Ymax_label = wx.StaticText(self, label="Y Max", style=wx.ALIGN_CENTER_VERTICAL)
        self.Ymax = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)

        self.auto_fit_button  = wx.Button(self, wx.ID_ANY, label="Auto fit")
        
        gbSizer0.Add(self.Xmin_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Xmin, (0,1), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ymin_label, (1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ymin, (1,1), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Xmax_label, (0,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Xmax, (0,3), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ymax_label, (1,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.Ymax, (1,3), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer0.Add(self.auto_fit_button, (2,1),span = (1,3), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        sbsizer0.Add(gbSizer0, 1, wx.EXPAND, 5)
        
        sb1 = wx.StaticBox(self, wx.ID_ANY, label = "Unit and Scale")
        sbsizer1 = wx.StaticBoxSizer(sb1, wx.VERTICAL)
        
        gbSizer1 = wx.GridBagSizer(5,5)
        
        self.Xscale_label = wx.StaticText(self, label="X", style=wx.ALIGN_CENTER_VERTICAL)
        self.Xscale = wx.ComboBox(self, id = wx.ID_ANY, choices=self.axis_scales_choices, style=wx.CB_READONLY)

        self.Xunit = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        self.Yscale_label = wx.StaticText(self, label="Y", style=wx.ALIGN_CENTER_VERTICAL)
        self.Yscale = wx.ComboBox(self, id = wx.ID_ANY, choices=self.axis_scales_choices, style=wx.CB_READONLY)

        self.Yunit = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        gbSizer1.Add(self.Xscale_label, (0,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Xunit, (0,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Xscale, (0,4), flag = wx.ALIGN_CENTER_VERTICAL)
       
        gbSizer1.Add(self.Yscale_label,(1,0), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Yunit, (1,2), flag = wx.ALIGN_CENTER_VERTICAL)
        gbSizer1.Add(self.Yscale, (1,4), flag = wx.ALIGN_CENTER_VERTICAL)
        
        sbsizer1.Add(gbSizer1, 1, wx.EXPAND, 5)
        
        hsizer0.Add(sbsizer0, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        hsizer0.Add(sbsizer1, 1, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

               
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button  = wx.Button(self, wx.ID_ANY, label="Apply")
        hsizer1.Add(self.apply_button, 0, wx.EXPAND, 0)
        
        Sizer.Add(hsizer0, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        Sizer.Add(hsizer1, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.ALL, 5)
        
        self.SetSizer(Sizer)        
        Sizer.Fit(self)
        self.Layout()
        
        self.Bind(wx.EVT_BUTTON, self.auto_fit, self.auto_fit_button)
        self.Bind(wx.EVT_BUTTON, self.set_settings, self.apply_button)
    
        self.get_settings()
    
    def get_settings(self, event = None):
        [Xmin, Xmax, Ymin, Ymax] = self.parent.figure.gca().axis()
        self.parent.Xmin = Xmin
        self.parent.Ymin = Ymin
        self.parent.Xmax = Xmax
        self.parent.Ymax = Ymax
        
        self.Xmin.SetValue(str(self.parent.Xmin))
        self.Ymin.SetValue(str(self.parent.Ymin))
        self.Xmax.SetValue(str(self.parent.Xmax))
        self.Ymax.SetValue(str(self.parent.Ymax))
         
        self.Xunit.SetValue(str(self.parent.Xunit))
        self.Yunit.SetValue(str(self.parent.Yunit))
         
        self.Xscale.SetValue(self.parent.Xscale)
        self.Yscale.SetValue(self.parent.Yscale)
        
    def set_settings(self, event = None):
        # CheckUnits. checkUnits method will raise exception if needed
        self.checkUnits(self.parent.Xunit, self.Xunit.GetValue())
        self.checkUnits(self.parent.Yunit, self.Yunit.GetValue())
        
        self.parent.Xunit = self.Xunit.GetValue()
        self.parent.Yunit = self.Yunit.GetValue()
         
        self.parent.figure.gca().set_xlabel(self.parent.Xlabel + self.parent.fmt_Xunit )
        self.parent.figure.gca().set_ylabel(self.parent.Ylabel + self.parent.fmt_Yunit )
         
        self.parent.Xscale = self.Xscale.GetValue()
        self.parent.Yscale = self.Yscale.GetValue()
         
        self.parent.scale_xAxis()
        self.parent.scale_yAxis()
         
        self.parent.Xmin = float(self.Xmin.GetValue())
        self.parent.Ymin = float(self.Ymin.GetValue())
        self.parent.Xmax = float(self.Xmax.GetValue())
        self.parent.Ymax = float(self.Ymax.GetValue())
         
        self.parent.figure.gca().axis([self.parent.Xmin, self.parent.Xmax, self.parent.Ymin, self.parent.Ymax])  
        
        self.parent.set_ticks()
        self.parent.canvas.draw()
    
    def auto_fit(self, event = None):
        self.parent.on_auto_fit(event=event)
        self.Xmin.SetValue(str(self.parent.Xmin))
        self.Ymin.SetValue(str(self.parent.Ymin))
        self.Xmax.SetValue(str(self.parent.Xmax))
        self.Ymax.SetValue(str(self.parent.Ymax))
    

class LinesSettingsDialog(wx.Dialog):
    
    def __init__(self, parent=None):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title="Lines Settings", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        self.parent = parent
        self.current_line = None
        self.build_dialog()
        
    def build_dialog(self):
        
        self.marker = ['o', '^','s', 'p' ,'*']
        
        self.style_choice = ['-' , '--' , '-.' , ':', 'None'] + self.marker
        
        Sizer = wx.BoxSizer(wx.VERTICAL)
        
        bagSizer    = wx.GridBagSizer(hgap=5, vgap=5)
        
        self.lines = wx.ListCtrl(self, wx.ID_ANY, style = wx.LC_REPORT)
        self.lines.InsertColumn(0, 'Lines')
        
        self.del_button  = wx.Button(self, wx.ID_ANY, label="Delete")
        
        self.color_label = wx.StaticText(self, label="Color" , style=wx.ALIGN_CENTER_VERTICAL)
        self.color_picker = wx.ColourPickerCtrl(self, id = wx.ID_ANY, col = 'black')
        
        self.legend_label = wx.StaticText(self, label="Legend" , style=wx.ALIGN_CENTER_VERTICAL)
        self.legend = wx.TextCtrl(self, wx.ID_ANY, style = wx.SL_HORIZONTAL|wx.TE_PROCESS_ENTER)
        
        self.style_label = wx.StaticText(self, label="Style", style=wx.ALIGN_CENTER_VERTICAL)
        self.style = wx.ComboBox(self, id = wx.ID_ANY, choices=self.style_choice, style=wx.CB_READONLY)
        
        self.width_label = wx.StaticText(self, label="Width" , style=wx.ALIGN_CENTER_VERTICAL)
        self.width = wx.SpinCtrl(self, id=wx.ID_ANY, style = wx.SP_ARROW_KEYS)
        
        bagSizer.Add(self.lines, pos=(0,0), span=(4,3), flag = wx.EXPAND)
        
        bagSizer.Add(self.del_button, pos=(4,0), span=(1,3), flag = wx.EXPAND)
        
        bagSizer.Add(self.legend_label, pos=(1,4), flag = wx.ALIGN_CENTER_VERTICAL)
        bagSizer.Add(self.legend, pos=(1,5) ,span=(1,5), flag = wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        bagSizer.Add(self.style_label, pos=(2,4), flag = wx.ALIGN_CENTER_VERTICAL)
        bagSizer.Add(self.style, pos=(2,5), flag = wx.ALIGN_CENTER_VERTICAL)
        
        bagSizer.Add(self.width_label, pos=(2,7), flag = wx.ALIGN_CENTER_VERTICAL)
        bagSizer.Add(self.width, pos=(2,8), flag = wx.ALIGN_CENTER_VERTICAL)
        
        bagSizer.Add(self.color_label, pos=(3,4), flag = wx.ALIGN_CENTER_VERTICAL)
        bagSizer.Add(self.color_picker, pos=(3,5), flag = wx.ALIGN_CENTER_VERTICAL)
        
        hsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.apply_button  = wx.Button(self, wx.ID_ANY, label="Apply")
        hsizer1.Add(self.apply_button, 0, wx.EXPAND, 0)
        
        Sizer.Add(bagSizer, 0, wx.EXPAND|wx.ALL, 5)
        Sizer.Add(hsizer1, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.ALL, 5)
          
        self.SetSizer(Sizer)        
        Sizer.Fit(self)
        self.Layout()
        
        self.Bind(wx.EVT_BUTTON, self.delete_line, self.del_button)
        self.Bind(wx.EVT_BUTTON, self.set_settings, self.apply_button)
        self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.on_select_item, self.lines)
    
        self.set_lines()
    
    def set_lines(self):
        self.lines.DeleteAllItems()
        _id = 0
        for k in self.parent.plots.keys():
            if type(self.parent.plots[k][0].get_color()) is str:
                try:
                    r,g,b = matplotlib.colors.colorConverter.colors[self.parent.plots[k][0].get_color()]
                except KeyError:
                    color = self.parent.plots[k][0].get_color().lstrip("#")
                    r,g,b = tuple(int(color[i:i+2], 16)/255.0 for i in (0, 2, 4))
            else:
                r,g,b = self.parent.plots[k][0].get_color()
            self.lines.InsertStringItem(index = _id, label = k)
            color = wx.Colour(int(r*255), int(g*255), int(b*255))
            self.lines.SetItemTextColour(_id, color)
            _id += 1
    
    def on_select_item(self, event):
        line_name = event.GetLabel()
        if not line_name:
            return
        self.current_line = self.parent.plots[line_name][0]
        if self.parent.selectedLine is not None: 
            self.parent.selectedLine.set_alpha(1.0)
            self.parent.figure.canvas.draw()

        # set new selection and alpha  
        self.parent.selectedLine = self.current_line
        self.parent.selectedLine.set_alpha(0.4)
        self.parent.figure.canvas.draw()
        
        if type(self.current_line.get_color()) is str:
            try:
                r,g,b = matplotlib.colors.colorConverter.colors[self.current_line.get_color()]
            except KeyError:
                color = self.current_line.get_color().lstrip("#")
                r,g,b = tuple(int(color[i:i+2], 16)/255.0 for i in (0, 2, 4))
        else:
            r,g,b = self.current_line.get_color()
        color = wx.Colour(int(r*255), int(g*255), int(b*255))
        self.color_picker.SetColour(color)
        self.legend.SetValue(self.parent.plots[line_name][1])
        self.style.SetValue(self.current_line.get_linestyle())
        self.width.SetValue(self.current_line.get_linewidth())
        
    def set_settings(self, event = None):
        if self.current_line is None:
            return
        
        color= self.color_picker.GetColour()
        self.current_line.set_color((color.Red()/255., color.Green()/255., color.Blue()/255.))
        for v in self.parent.plots.values():
            if v[0] is self.current_line:
                new_legend = self.legend.GetValue()
                if new_legend != v[1]:
                    v[1] = new_legend
                    self.parent.update_legend()
        s = self.style.GetValue()
        if s in self.marker:
            self.current_line.set_linestyle('None')
            self.current_line.set_marker(s)
        else:
            self.current_line.set_marker('')
            self.current_line.set_linestyle(self.style.GetValue())
        self.current_line.set_linewidth(self.width.GetValue())
        if self.parent.show_legend:
            self.parent.update_legend()
        self.parent.canvas.draw()
        self.set_lines()
        
    def delete_line(self, event = None):
        if self.parent.delete_line(self.current_line):
            self.parent.selectedLine = None
        self.set_lines()
