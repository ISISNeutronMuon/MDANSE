import collections
import os

import wx
import wx.combo
import wx.lib.filebrowsebutton as wxfile

class CheckboxComboPopup(wx.combo.ComboPopup):
    
    def __init__(self, items, maxNumberOfItems=None):
        
        wx.combo.ComboPopup.__init__(self)
        self._items = items
        self._maxNumberOfItems = maxNumberOfItems
        
        
    @property
    def items(self):
        return self._items

    @property
    def checklistbox(self):
        
        return self._checklistbox
        
    def Create(self, parent):    
        self._checklistbox = wx.CheckListBox(parent, -1, choices=self._items)
        self._checklistbox.Bind(wx.EVT_CHECKLISTBOX, self.on_check_item)
        if not self._checklistbox.IsEmpty():
            self._checklistbox.Check(0)
                
        return True
    
    
    def GetControl(self):
        return self._checklistbox
    
        
    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        return self._checklistbox.GetSize()
    
    
    def GetStringValue(self): 
        return self._checklistbox.GetCheckedStrings()
    

    def on_check_item(self, event):
        
        if self._maxNumberOfItems is None:
            return
                
        nCheckedItems = len(self._checklistbox.GetChecked())
        
        if nCheckedItems > self._maxNumberOfItems:
            self._checklistbox.Check(event.GetInt(), False)
                

class ComboPanel(wx.Panel):
        
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
    

class ComboCheckableMenu(ComboPanel):
    
    def __init__(self, parent, choices, exclusive=False, labelText="", menuText="", *args, **kwargs):
        
        ComboPanel.__init__(self, parent, *args, **kwargs)
                
        self._choices = collections.OrderedDict().fromkeys(choices, False)
        
        self._exclusive = exclusive
                        
        self._labelText = labelText
        
        self._menuText = menuText
        
        self.build_panel()
        
        self.build_layout()
                        
        
    def build_panel(self):
    
        self._button = self.create_menubutton()
        
    
    def build_layout(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add(self._button, 1, flag=wx.EXPAND)
        
        self.SetSizer(sizer)


    def create_menubutton(self):
        
        button = wx.Button(self, wx.ID_ANY, label=self._menuText)
        button.Bind(wx.EVT_BUTTON, self.on_display_menu)
        
        return button
        
        
    def get_value(self):
        
        selection = [label for label,state in self._choices.items() if state]
        
        return selection
        
    
    def on_check_menuitem(self, event):

        for item in event.GetEventObject().GetMenuItems():
            self._choices[item.GetLabel()] = item.IsChecked()
            
        if self._exclusive:
            item = event.GetEventObject().FindItemById(event.GetId())
            self._button.SetLabel(item.GetLabel())
        
                                        
    def on_display_menu(self, event):

        menu = wx.Menu()
                
        for label, state in self._choices.items():
            if self._exclusive:
                item = menu.AppendRadioItem(wx.ID_ANY, label)
            else:
                item = menu.AppendCheckItem(wx.ID_ANY, label)
            item.Check(state)

        x,y = self._button.GetPosition()
        w,h = self._button.GetSize()

        self.Bind(wx.EVT_MENU, self.on_check_menuitem)

        self._button.PopupMenu(menu, (x+w/2,y+h/2))
        

class ComboCheckbox(ComboPanel):

    def __init__(self,
                 parent,
                 parameters=None,
                 sizerParameters=None,
                 checked=False,
                 *args, **kwargs):

        ComboPanel.__init__(self, parent, *args, **kwargs)
                
        self._parameters = parameters
        
        self._checked = checked
                            
        if sizerParameters is None:
            sizerParameters = {"hgap" : 5, "vgap" : 5}
        self._sizerParameters = sizerParameters
                
        self.build_panel()
        
        self.build_layout()

        self.on_toggle_checkbox_state()
        

    def build_panel(self):

        check = self._parameters.setdefault("check",{})
        
        cParams = check.setdefault("w_parameters",{})
                        
        self._checkbox = wx.CheckBox(self, **cParams)

        self._widget = self._parameters.setdefault("widget",None)
        
        if self._widget is not None:
            widget, wParams = self._widget
            wParams.setdefault("w_parameters",{})
            self._widget = widget(self, **wParams["w_parameters"])
        
        self._checkbox.SetValue(self._checked)
        
        self._checkbox.Bind(wx.EVT_CHECKBOX, self.on_toggle_checkbox_state)

    def build_layout(self):

        sizer = wx.GridBagSizer(**self._sizerParameters)
                                                    
        sParams = self._parameters["check"].setdefault("s_parameters",{})
        sizer.Add(self._checkbox, **sParams)
                    
        if self._widget is not None:
            sParams = self._parameters["widget"][1].setdefault("s_parameters",{})
            sizer.Add(self._widget, **sParams)
        
        self.SetSizer(sizer)
        
        
    def get_value(self):
        
        checked = self._checkbox.GetValue()
        
        if checked:
            
            try:
                value = self._widget.get_value()
            except AttributeError:
                try:
                    value = self._widget.GetValue()
                except AttributeError:        
                    value = None
                    
        else:
            value = None
            
        return (checked,value)
        
    
    def on_toggle_checkbox_state(self, event=None):
        
        checked = self._checkbox.GetValue()
        
        try:
            self._widget.Enable(checked)
        except:
            pass


class ComboOutputFile(ComboPanel):
    
    def __init__(self, parent, formats, sizerParameters=None, *args, **kwargs):

        ComboPanel.__init__(self, parent, *args, **kwargs)
        
        self._formats = formats
        
        if sizerParameters is None:
            sizerParameters = {"hgap" : 5, "vgap" : 5}
        self._sizerParameters = sizerParameters
        
        self.build_panel()
        
        self.build_layout()
        
    
    @property
    def directory(self):
        return self._directory
    

    @property
    def basename(self):
        return self._basename
    

    def build_panel(self):
        
        self._directory = wxfile.DirBrowseButton(self, labelText="Directory", startDirectory=os.getcwd(), newDirectory=True)
        
        self._directory.label.SetWindowStyle(wx.ALIGN_LEFT)
        
        self._basenameLabel = wx.StaticText(self, label="Basename", style=wx.ALIGN_LEFT)
        
        self._basename = wx.TextCtrl(self, value="")
        
        self._formats = ComboCheckableMenu(self, self._formats, labelText="File formats", menuText="Formats")
        
                
    def build_layout(self):
 
        sizer = wx.GridBagSizer(**self._sizerParameters)
        
        sizer.Add(self._directory, pos=(0,0), span=(1,3), flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

        sizer.Add(self._basenameLabel, pos=(1,0), flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(self._basename, pos=(1,1), flag=wx.EXPAND)

        sizer.Add(self._formats, pos=(1,2), flag=wx.EXPAND)
 
        sizer.AddGrowableCol(1)
 
        self.SetSizer(sizer)
        
        
    def get_value(self):
        
        directory = self._directory.GetValue()
        basename = self._basename.GetValue().strip()

        if not basename:
            raise ValueError("No basename for the output file provided.")
                
        formats = self._formats.get_value()
        
        if not formats:
            raise ValueError("No output formats selected.")
                            
        return (directory, basename, formats)
        

class ComboRadioButtons(ComboPanel):

    def __init__(self,
                 parent,
                 parameters,
                 sizerParameters=None,
                 selected=0,
                 *args, **kwargs):
                
        ComboPanel.__init__(self, parent, *args, **kwargs)
                
        self._parameters = parameters
                             
        if sizerParameters is None:
            sizerParameters = {"hgap" : 5, "vgap" : 5}
        self._sizerParameters = sizerParameters

        self._selected = selected

        self._radios = []
        self._widgets = []
                
        self.build_panel()
        
        self.build_layout()
        
        
    def add_radiobutton(self, parameters):
        
        radio = parameters.setdefault("radio",{})
        
        rParams = radio.setdefault("w_parameters",{})
                
        self._radios.append(wx.RadioButton(self, **rParams))
                        
        widget = parameters.setdefault("widget",None)
        
        if widget is not None:
            widget, wParams = widget
            wParams.setdefault("w_parameters",{})
            widget = widget(self, **wParams["w_parameters"])
                
        self._widgets.append(widget)
        
        self._radios[-1].Bind(wx.EVT_RADIOBUTTON, self.on_select_radiobutton)
                

    def build_panel(self):
        
        for params in self._parameters:
            self.add_radiobutton(params)
            
        self._radios[0].SetWindowStyle(wx.RB_GROUP)
        self._radios[self._selected].SetValue(True)
        self.select_radiobutton(self._selected)
            
        
    def build_layout(self):

        sizer = wx.GridBagSizer(**self._sizerParameters)
                                        
        for p, r, w in zip(self._parameters, self._radios, self._widgets):
            
            sParam = p["radio"].setdefault("s_parameters",{})
            sizer.Add(r, **sParam)
                    
            if w is not None:
                sParam = p["widget"][1].setdefault("s_parameters",{})
                sizer.Add(w, **sParam)
        
        self.SetSizer(sizer)


    def get_selected_radiobutton(self):
        
        idx = [i for i, r in enumerate(self._radios) if r.GetValue()][0]
        
        return idx


    def get_value(self):
        
        label = str(self._radios[self._selected].GetLabel())
        
        try:
            value = self._widgets[self._selected].get_value()
        except AttributeError:
            try:
                value = self._widgets[self._selected].GetValue()
            except AttributeError:        
                value = None
                
        return (label,value)
        
            
    def on_select_radiobutton(self, event=None):

        self._selected = self._radios.index(event.GetEventObject())
        
        self.select_radiobutton(self._selected)
        
                
    def select_radiobutton(self, idx):

        for i,w in enumerate(self._widgets):
            try:
                w.Enable(i==idx)
            except:
                pass
            

class ComboRange(ComboPanel):
        
    def __init__(self, parent, type=int, *args, **kwargs):
        
        ComboPanel.__init__(self, parent, *args, **kwargs)
        
        self._type = type

        self.build_panel()
        
        self.build_layout()
    
    
    @property
    def first(self):
        return self._first
    

    @property
    def last(self):
        return self._last


    @property
    def step(self):
        return self._step
    
    
    def build_panel(self):
        
        self._first = ComboWidget(self,
                                  wx.TextCtrl,
                                  widgetSizerParameters={"proportion" : 1, "border" : 5, "flag" : wx.ALL|wx.EXPAND},
                                  label="First",
                                  labelSizerParameters = {"flag" : wx.ALIGN_CENTER_VERTICAL})
        
        self._last = ComboWidget(self,
                                 wx.TextCtrl,
                                 widgetSizerParameters={"proportion" : 1, "border" : 5, "flag" : wx.ALL|wx.EXPAND},
                                 label="Last",
                                 labelSizerParameters = {"flag" : wx.ALIGN_CENTER_VERTICAL}) 
        
        self._step = ComboWidget(self,
                                 wx.TextCtrl,\
                                 widgetSizerParameters={"proportion" : 1, "border" : 5, "flag" : wx.ALL|wx.EXPAND},
                                 label="Step",
                                 labelSizerParameters = {"flag" : wx.ALIGN_CENTER_VERTICAL}) 


    def build_layout(self):

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        sizer.Add(self._first, 1, wx.ALL|wx.EXPAND, 5)        
        sizer.Add(self._last, 1, wx.ALL|wx.EXPAND, 5)        
        sizer.Add(self._step, 1, wx.ALL|wx.EXPAND, 5)

        self.SetSizer(sizer)
        
        
    def get_value(self):
        
        f = self._type(self._first.get_value())
        l = self._type(self._last.get_value())
        s = self._type(self._step.get_value())
        
        return (f,l,s)
                

class ComboWidget(ComboPanel):
    
    def __init__(self, 
                 parent, 
                 widget, 
                 widgetParameters=None, 
                 widgetSizerParameters=None,
                 label="", 
                 labelParameters=None, 
                 labelSizerParameters=None, 
                 icon=None, 
                 iconSizerParameters=None, *args, **kwargs):    

        ComboPanel.__init__(self, parent, *args, **kwargs)
        
        # The widget part
        self._widget = widget
        
        if widgetParameters is None:
            widgetParameters = {"style" : wx.EXPAND}
        self._widgetParameters = widgetParameters

        if not isinstance(widgetSizerParameters,dict):
            widgetSizerParameters = {"proportion" : 1, "flag" : wx.ALIGN_CENTER_VERTICAL}
        self._widgetSizerParameters = widgetSizerParameters

        self._label = label
        
        if labelParameters is None:
            labelParameters = {"style" : wx.EXPAND}
        self._labelParameters = labelParameters

        if labelSizerParameters is None:
            labelSizerParameters = {"proportion" : 0, "flag" : wx.ALIGN_CENTER_VERTICAL}
        self._labelSizerParameters = labelSizerParameters
        
        # The icon part
        self._icon = icon
        if not isinstance(iconSizerParameters,dict):
            iconSizerParameters = {}
        self._iconSizerParameters = iconSizerParameters
        
        self.build_panel()
        
        self.build_layout()
        

    def build_panel(self):
        
        self._label = wx.StaticText(self, wx.ID_ANY, self._label, **self._labelParameters)
                
        self._widget = self._widget(self, **self._widgetParameters)        

        if self._icon is not None:
            self._icon = wx.ArtProvider.GetBitmap(self._icon, wx.ID_ANY, **self._iconParameters)


    def build_layout(self):

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self._icon is not None:
            sizer.Add(self._icon, **self._iconSizerParameters)
        
        sizer.Add(self._label, **self._labelSizerParameters)
        
        sizer.Add(self._widget, **self._widgetSizerParameters)
        
        self.SetSizer(sizer)        
        sizer.Fit(self)
        self.Layout()
        
    
    @property
    def widget(self):
        return self._widget
    

    @property
    def label(self):
        return self._label


    @property
    def icon(self):
        
        return self._icon


    def get_value(self):
        
        try:
            value = self._widget.GetValue()
            
        except AttributeError:
            value = None
            
        return value
            

                
if __name__ == "__main__":
    
    app = wx.App(False)
    
    f = wx.Frame(None)
    
    panel = wx.Panel(f, wx.ID_ANY)
    s = wx.BoxSizer(wx.VERTICAL)
    
    p = ComboWidget(panel, wx.TextCtrl, label="ddada")
    s.Add(p, 0, wx.EXPAND)

    p = ComboRadioButtons(panel,
                          parameters = [{"radio"  : {"w_parameters" : {"label":"r1"}, 
                                                     "s_parameters" : {"pos" : (0,0)}},
                                         "widget" : [wx.TextCtrl, {"w_parameters" : {"value":"ddakjdlksajd"}, 
                                                                   "s_parameters" : {"pos" : (1,1)}}]}, 
                                        {"radio" : {"w_parameters" : {"label":"r2"}, 
                                                    "s_parameters" : {"pos" : (2,0)}}}])
    
    s.Add(p, 0, wx.EXPAND)

    p = ComboCheckbox(panel,
                          parameters = {"check"  : {"w_parameters" : {"label":"r1"},
                                                    "s_parameters" : {"pos" : (0,0)}},
                                        "widget" : [wx.TextCtrl, {"w_parameters" : {"value":"ddakjdlksajd"},
                                                                  "s_parameters" : {"pos" : (1,1)}}]})
    
    s.Add(p, 0, wx.EXPAND)

    p = ComboOutputFile(panel, ["netcdf","svg","ascii"])    
    s.Add(p, 0, wx.EXPAND)

    p = ComboRange(panel)    
    s.Add(p, 0, wx.EXPAND)

    panel.SetSizer(s)
    
    f.Show()
        
    app.MainLoop()
        
        