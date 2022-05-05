# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/UserDefinitionViewer.py
# @brief     Implements module/class/test UserDefinitionViewer
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import copy

import wx

from MDANSE import LOGGER
from MDANSE.Framework.Units import _UNAMES, UNITS_MANAGER

class FloatValidator(wx.PyValidator):
    """ This validator is used to ensure that the user has entered a float
        into the text control of MyFrame.
    """
    def __init__(self):
        """ Standard constructor.
        """
        wx.PyValidator.__init__(self)

    def Clone(self):
        """ Standard cloner.

            Note that every validator must implement the Clone() method.
        """
        return FloatValidator()

    def Validate(self, win):
        textCtrl = self.GetWindow()
        num_string = textCtrl.GetValue()
        try:
            float(num_string)
        except:
            wx.MessageBox("Please enter numbers only", "Invalid Input", wx.OK | wx.ICON_ERROR)
            return False
        else:
            return True

    def TransferToWindow(self):
        """ Transfer data from validator to window.

            The default implementation returns False, indicating that an error
            occurred.  We simply return True, as we don't do any data transfer.
        """
        return True


    def TransferFromWindow(self):
        """ Transfer data from window to validator.

            The default implementation returns False, indicating that an error
            occurred.  We simply return True, as we don't do any data transfer.
        """
        return True

class NewUnitDialog(wx.Dialog):
    """
    This class pops up a dialog that prompts the user for registering a new element in the database.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor.
        """

        # The base class constructor
        wx.Dialog.__init__(self, *args, **kwargs)

        self.Center()

        # Create text and answer box widgets
        staticLabel = wx.StaticText(self, wx.ID_ANY, "Unit name")
        self._unit = wx.TextCtrl(self, wx.ID_ANY)

        self._labels = collections.OrderedDict()
        self._dimensions = collections.OrderedDict()
        for uname in _UNAMES:
            self._labels[uname] = wx.StaticText(self,label=uname)
            self._dimensions[uname] = wx.SpinCtrl(self,id=wx.ID_ANY,style=wx.SP_WRAP)
            self._dimensions[uname].SetRange(-100,100)
            self._dimensions[uname].SetValue(0)
    
        factorLabel = wx.StaticText(self,label='Factor')
        self._factor = wx.TextCtrl(self, wx.ID_ANY, style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB,validator=FloatValidator())
        self._factor.SetValue('1.0')

        # Create buttons
        ok = wx.Button(self, wx.ID_OK, "OK")
        ok.SetDefault()
        cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")

        # Create main sizer and add the instruction text to the top
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        unitNameSizer = wx.BoxSizer(wx.HORIZONTAL)
        unitNameSizer.Add(staticLabel, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        unitNameSizer.Add(self._unit, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)

        factorSizer = wx.BoxSizer(wx.HORIZONTAL)
        factorSizer.Add(factorLabel, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        factorSizer.Add(self._factor, 1, wx.ALL, 5)

        dimensionsSizer = wx.GridBagSizer(5,5)
        for comp, k in enumerate(self._dimensions):
            dimensionsSizer.Add(self._labels[k], (comp,0),flag=wx.ALIGN_CENTER_VERTICAL)
            dimensionsSizer.Add(self._dimensions[k], (comp,1),flag=wx.EXPAND)
        dimensionsSizer.AddGrowableCol(1)

        # Place buttons to appear as a standard dialogue
        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(cancel)
        button_sizer.AddButton(ok)
        button_sizer.Realize()

        main_sizer.Add(unitNameSizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(factorSizer, 0, wx.ALIGN_LEFT | wx.EXPAND, 5)
        main_sizer.Add(dimensionsSizer, 0, wx.ALL | wx.EXPAND, 5)
        main_sizer.Add(button_sizer, 0, wx.EXPAND)

        # Give a minimum size for the dialog but ensure that everything fits inside
        self.SetMinSize(wx.Size(400, 160))
        self.SetSizerAndFit(main_sizer)
        self.Fit()

    def GetValue(self, event=None):
        """
        Handler called when the user clicks on the OK button of the property dialog.
        """

        unit = str(self._unit.GetValue().strip())

        factor = float(self._factor.GetValue())

        dim = [v.GetValue() for v in self._dimensions.values()]

        return unit, factor, dim

class UnitsEditor(wx.Dialog):
    
    def __init__(self, parent, title="Units Editor", standalone=False):
        
        wx.Dialog.__init__(self, parent, wx.ID_ANY, size = (600,500), title = title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)
        
        self._standalone = standalone

        self._dialogSizer = wx.BoxSizer(wx.VERTICAL)

        self._build()

    def _build(self):

        mainPanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())        

        self._defaultUnits = copy.deepcopy(UNITS_MANAGER.units)

        self._unitsList = wx.ListBox(mainPanel, wx.ID_ANY, choices = sorted(self._defaultUnits.keys()), style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_EDIT_LABELS)
                
        self._cancel  = wx.Button(mainPanel, wx.ID_ANY, label="Cancel")
        self._save  = wx.Button(mainPanel, wx.ID_ANY, label="Save")
        self._ok  = wx.Button(mainPanel, wx.ID_ANY, label="OK")

        factorPanel = wx.Panel(mainPanel,wx.ID_ANY)
        factorLabel = wx.StaticText(factorPanel,label='Factor')
        self._factor = wx.TextCtrl(factorPanel, wx.ID_ANY, style=wx.TE_PROCESS_ENTER|wx.TE_PROCESS_TAB,validator=FloatValidator())

        dimensionsPanel = wx.Panel(mainPanel,wx.ID_ANY)
        self._labels = collections.OrderedDict()
        self._dimensions = collections.OrderedDict()
        for uname in _UNAMES:
            self._labels[uname] = wx.StaticText(dimensionsPanel,label=uname)
            self._dimensions[uname] = wx.SpinCtrl(dimensionsPanel,id=wx.ID_ANY,style=wx.SP_WRAP)
            self._dimensions[uname].SetRange(-100,100)
            self._dimensions[uname].SetValue(0)
    
        addUnit = wx.Button(mainPanel,wx.ID_ANY,label='Add unit')

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        factorSizer = wx.BoxSizer(wx.HORIZONTAL)
        factorSizer.Add(factorLabel, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        factorSizer.Add(self._factor, 1, wx.ALL, 5)
        factorPanel.SetSizer(factorSizer)

        dimensionsSizer = wx.GridBagSizer(len(_UNAMES),2)
        for comp, k in enumerate(self._dimensions):
            dimensionsSizer.Add(self._labels[k], (comp,0),flag=wx.ALIGN_CENTER_VERTICAL)
            dimensionsSizer.Add(self._dimensions[k], (comp,1),flag=wx.EXPAND)
        dimensionsSizer.AddGrowableCol(1)
        dimensionsPanel.SetSizer(dimensionsSizer)

        unitsSizer = wx.BoxSizer(wx.VERTICAL)
        unitsSizer.Add(self._unitsList, 1, wx.ALL|wx.EXPAND, 5)
        unitsSizer.Add(addUnit, 0, wx.ALL|wx.EXPAND, 5)

        infoSizer = wx.BoxSizer(wx.HORIZONTAL)
        infoSizer.Add(unitsSizer, 1, wx.ALL|wx.EXPAND, 5)
        infoSizer.Add(factorPanel, 1, wx.ALL, 5)
        infoSizer.Add(dimensionsPanel, 1, wx.ALL|wx.EXPAND, 5)

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsSizer.Add(self._cancel,0,wx.ALL,5)
        buttonsSizer.Add(self._save,0,wx.ALL,5)
        buttonsSizer.Add(self._ok,0,wx.ALL,5)

        mainSizer.Add(infoSizer,1,wx.ALL|wx.EXPAND,5)                      
        mainSizer.Add(buttonsSizer,0,wx.ALL|wx.ALIGN_RIGHT,5)                      
        mainPanel.SetSizer(mainSizer)
                
        self.Bind(wx.EVT_LISTBOX,self.on_select_unit,self._unitsList)
        self.Bind(wx.EVT_CLOSE, self.on_close,self)
        self.Bind(wx.EVT_BUTTON, self.on_close,self._cancel)
        self.Bind(wx.EVT_BUTTON, lambda evt : self.on_ok(evt,True), self._save)
        self.Bind(wx.EVT_BUTTON, lambda evt : self.on_ok(evt,False), self._ok)
        self._factor.Bind(wx.EVT_KILL_FOCUS,self.on_change_unit)
        self._factor.Bind(wx.EVT_TEXT_ENTER,self.on_change_unit)
        self._unitsList.Bind(wx.EVT_KEY_DOWN, self.on_delete_unit)
        self.Bind(wx.EVT_BUTTON, self.on_add_unit, addUnit)

        for v in self._dimensions.values():
            self.Bind(wx.EVT_SPINCTRL,self.on_change_unit,v)

        self._dialogSizer.Add(mainPanel,1,wx.EXPAND)
        
        self.SetSizer(self._dialogSizer)

    def validate(self):

        if not self._factor.GetValidator().Validate(self._factor):
            return False

        else:
            return True
            
    def on_add_unit(self,event):

        d = NewUnitDialog(self, title="Add unit", size=(400, 220))

        # If the new element dialog is closed by clicking on OK.
        if d.ShowModal() == wx.ID_CANCEL:
            return

        # Get rid of wxpython unicode string formatting
        unitName, factor, dimension = d.GetValue()
        if not unitName:
            return

        if UNITS_MANAGER.has_unit(unitName):
            d = wx.MessageDialog(None, 'This unit already exists. Do you want to overwrite it ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
            if d.ShowModal() == wx.ID_NO:
                return

        UNITS_MANAGER.add_unit(unitName,factor,*dimension)

        units = sorted(UNITS_MANAGER.units.keys())
        self._unitsList.SetItems(units)

    def on_change_unit(self, event):

        if self._unitsList.GetSelection() < 0:
            return

        selected_unit = self._unitsList.GetString(self._unitsList.GetSelection())
        if not selected_unit:
            return

        dim = [v.GetValue() for v in self._dimensions.values()]

        if not self.validate():
            return

        factor = float(self._factor.GetValue())

        UNITS_MANAGER.add_unit(selected_unit,factor,*dim)

    def on_close(self,event):

        UNITS_MANAGER.units = self._defaultUnits

        self.EndModal(wx.CANCEL)

        self.Destroy()

    def on_delete_unit(self,event):

        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:

            idx = self._unitsList.GetSelection()
            selected_unit = self._unitsList.GetString(idx)
            UNITS_MANAGER.delete_unit(selected_unit)
            self._unitsList.Delete(idx)

    def on_select_unit(self,event):

        selected_unit = self._unitsList.GetString(self._unitsList.GetSelection())
        selected_unit = UNITS_MANAGER.get_unit(selected_unit)

        self._factor.SetValue(str(selected_unit.factor))

        dim = selected_unit.dimension
        for k,v in zip(_UNAMES,dim):
            self._dimensions[k].SetValue(v)
            
    def on_ok(self,event,save=False):

        if save:
            UNITS_MANAGER.save()
            if self._standalone:
                wx.MessageBox("Units database saved successfully", "Success", wx.OK | wx.ICON_INFORMATION)
            else:
                LOGGER("Units database saved successfully","info")
                self.Destroy()
        else:
            self.Destroy()

if __name__ == "__main__":
    app = wx.App(False)
    f = UnitsEditor(None)
    f.ShowModal()
    f.Destroy()
    app.MainLoop()
