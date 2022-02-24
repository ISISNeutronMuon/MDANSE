# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/ElementsDatabaseEditor.py
# @brief     Implements module/class/test ElementsDatabaseEditor
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

import wx
import wx.grid as wxgrid

from MDANSE import ELEMENTS, PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

def create_mmtk_atom_entry(entryname, name, symbol, mass, **props):
    '''
    Creates a new atom in mmtk database.

    :param name: the basename of the file in which the atom entry will be stored
    :type name: str
    :param symbol:
    :type symbol: str
    :param mass: the mass of the atom
    :type mass: float

    :return: the absolute path of the file that stores the newly created atom
    :rtype: str
    '''

    # Every entry of the MMTK database is searched in lower case.
    entryname = entryname.lower()

    filename = os.path.join(PLATFORM.local_mmtk_database_directory(),"Atoms", entryname)

    f = open(filename, 'w')
    # This three entries are compulsory for a MMTK.Atom to be valid
    f.write('name = "%s"' % name)
    f.write('\n\nsymbol = "%s"' % symbol)
    f.write('\n\nmass = %f' % mass)

    for k,v in props.items():
        f.write('\n\n%s = %r' % (k,v))

    f.close()

    return filename

class ElementsDatabaseError(Error):
    pass

class NewElementDialog(wx.Dialog):
    """
    This class pops up a dialog that prompts the user for registering a new element in the database.
    """

    def __init__(self,*args,**kwargs):
        """
        The constructor.
        """

        # The base class constructor
        wx.Dialog.__init__(self,*args,**kwargs)

        self.Center()

        panel = wx.Panel(self,wx.ID_ANY)

        # Create text and answer box widgets
        staticLabel0 = wx.StaticText(panel, -1, "Enter element settings")
        staticLabel1 = wx.StaticText(panel, wx.ID_ANY, "Entry name")
        self._entry = wx.TextCtrl(panel, wx.ID_ANY)
        staticLabel2 = wx.StaticText(panel, wx.ID_ANY, "Atom name")
        self._name = wx.TextCtrl(panel, id = wx.ID_ANY)
        staticLabel3 = wx.StaticText(panel, wx.ID_ANY, "Atom symbol")
        self._symbol = wx.TextCtrl(panel, wx.ID_ANY)
        staticLabel4 = wx.StaticText(panel, wx.ID_ANY, "Atom Mass (uma)")
        self._mass = wx.TextCtrl(panel, id = wx.ID_ANY)

        # Create buttons
        ok = wx.Button(panel, wx.ID_OK, "OK")
        ok.SetDefault()
        cancel = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        # Create main sizer and add the instruction text to the top
        main_sizer = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        main_sizer.Add(staticLabel0, 0, wx.ALL|wx.ALIGN_LEFT, 5)

        # Place the other text and answer box widgets in a grid
        body_sizer = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=20)
        body_sizer.Add(staticLabel1,flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=10)
        body_sizer.Add(self._entry ,flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.EXPAND, border=10)
        body_sizer.Add(staticLabel2,flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=10)
        body_sizer.Add(self._name  ,flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.EXPAND, border=10)
        body_sizer.Add(staticLabel3,flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=10)
        body_sizer.Add(self._symbol,flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.EXPAND, border=10)
        body_sizer.Add(staticLabel4,flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=10)
        body_sizer.Add(self._mass  ,flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.EXPAND, border=10)
        main_sizer.Add(body_sizer, 0, wx.ALL|wx.EXPAND, 5)

        # Place buttons to appear as a standard dialogue
        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(cancel)
        button_sizer.AddButton(ok)
        main_sizer.Add(button_sizer, 0, wx.EXPAND)
        button_sizer.Realize()

        # Add growth properties
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)
        body_sizer.AddGrowableCol(1)

        # Give a minimum size for the dialog but ensure that everything fits inside
        self.SetMinSize(wx.Size(400,160))
        panel.SetSizerAndFit(main_sizer)
        self.Fit()

    def GetValue(self, event=None):
        """
        Handler called when the user clicks on the OK button of the property dialog.
        """

        entry = str(self._entry.GetValue().strip())
        if not entry:
            raise ElementsDatabaseError("Empty entry name")

        name = str(self._name.GetValue().strip())
        if not name:
            raise ElementsDatabaseError("Empty name")

        symbol = str(self._symbol.GetValue().strip())
        if not symbol:
            raise ElementsDatabaseError("Empty symbol")

        try:
            mass = float(self._mass.GetValue().strip())
        except ValueError:
            raise ElementsDatabaseError("Invalid mass value")

        return entry,name,symbol,mass

class NewPropertyDialog(wx.Dialog):
    """
    This class pops up a dialog that prompts the user for registering a new property in the database.
    """

    def __init__(self,*args,**kwargs):
        """
        The constructor.
        """

        # The base class constructor
        wx.Dialog.__init__(self,*args,**kwargs)

        self.Center()

        panel = wx.Panel(self,wx.ID_ANY)
        main_sizer = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)

        # Add instructions
        title_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(title_sizer, 0, wx.EXPAND)
        title = wx.StaticText(panel, -1, "Enter property settings")
        title_sizer.Add(title, 0, wx.ALL | wx.ALIGN_LEFT, 5)

        # Add the body; ie the fields to fill in for the property
        body_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=15, hgap=20)
        main_sizer.Add(body_sizer, 0, wx.EXPAND)
        name_text = wx.StaticText(panel, wx.ID_ANY, "Name")
        self.name = wx.TextCtrl(panel, wx.ID_ANY)
        body_sizer.Add(name_text, 0, wx.ALIGN_LEFT | wx.LEFT, 10)
        body_sizer.Add(self.name, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT, 10)

        property_text = wx.StaticText(panel, wx.ID_ANY, "Numeric type")
        self.propertyType = wx.ComboBox(panel, id = wx.ID_ANY, choices=ELEMENTS._TYPES.keys(), style=wx.CB_READONLY)
        body_sizer.Add(property_text, 0, wx.ALIGN_LEFT | wx.LEFT, 10)
        body_sizer.Add(self.propertyType, 0, wx.ALIGN_LEFT |  wx.EXPAND | wx.RIGHT, 10)

        # Add buttons
        button_sizer = wx.StdDialogButtonSizer()
        main_sizer.Add(button_sizer, 0, wx.EXPAND)
        cancel = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        button_sizer.AddButton(cancel)

        ok = wx.Button(panel, wx.ID_OK, "OK")
        ok.SetDefault()
        button_sizer.AddButton(ok)
        button_sizer.Realize()

        # Allow for changing size
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(1)
        body_sizer.AddGrowableCol(1)

        # Give a minimum size for the dialog but ensure that everything fits inside
        self.SetMinSize(wx.Size(400, 160))
        panel.SetSizerAndFit(main_sizer)
        self.Fit()

    def GetValue(self, event=None):
        """
        Handler called when the user clicks on the OK button of the property dialog.
        """

        pname = str(self.name.GetValue().strip())

        pdefault = str(self.propertyType.GetValue())

        return pname,pdefault

class Database(wxgrid.PyGridTableBase):

    __metaclass__ = Singleton

    def GetColLabelValue(self, col):

        return "%s" % ELEMENTS.properties[col]

    def GetNumberCols(self):
        return ELEMENTS.nProperties

    def GetNumberRows(self):
        return ELEMENTS.nElements

    def GetRowLabelValue(self, row):

        return ELEMENTS.elements[row]

    def GetValue(self, row, col):

        return ELEMENTS[ELEMENTS.elements[row],ELEMENTS.properties[col]]

    def SetValue(self, row, col, val):

        ELEMENTS[ELEMENTS.elements[row],ELEMENTS.properties[col]] = val

    def add_column(self, pname,pdefault):

        ELEMENTS.add_property(pname, pdefault)

        self.notify_grid(wxgrid.GRIDTABLE_NOTIFY_COLS_APPENDED, 1)

    def add_row(self, entry, name, symbol, mass):

        if ELEMENTS.has_element(entry):
            return

        create_mmtk_atom_entry(entry, name, symbol, mass)

        ELEMENTS.add_element(entry)
        ELEMENTS[entry,"name"] = name
        ELEMENTS[entry,"symbol"] = symbol
        ELEMENTS[entry,"atomic_weight"] = mass

        self.notify_grid(wxgrid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)

    def notify_grid(self, msg, count):
        "Notifies the grid of the message and the affected count."

        tbl_msg = wxgrid.GridTableMessage(self, msg, count)

        self.GetView().ProcessTableMessage(tbl_msg)

    def saveas(self,fmt,filename):

        ELEMENTS.export(fmt,filename)

    def save(self, fmt="csv", filename=None):

        ELEMENTS.save()

class ElementsDatabaseEditor(wx.Frame):

    def __init__(self, parent):
        """
        The constructor.
        :Parameters:
            #. parent  (wx window): the parent window.
        """

        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Elements database editor", style=wx.DEFAULT_FRAME_STYLE|wx.RESIZE_BORDER)

        self._database = Database()

        self.build_dialog()

        self.build_menu()

        self.CenterOnParent()

    def build_dialog(self):

        mainPanel = wx.Panel(self,wx.ID_ANY)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # The wx grid that will store the database.            
        self._grid = wxgrid.Grid(mainPanel)

        # The grid style is set. This will be a standard text editor.
        self._grid.SetDefaultEditor(wxgrid.GridCellTextEditor())

        self._grid.SetTable(self._database)

        self._grid.SetDefaultCellBackgroundColour(wx.NamedColour("LIGHT BLUE"))

        self._grid.SetColLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        self._grid.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        self._grid.SetColMinimalAcceptableWidth(100)

        self._grid.Bind(wxgrid.EVT_GRID_CELL_CHANGE,self.on_edit_cell)
        self._grid.Bind(wxgrid.EVT_GRID_CELL_RIGHT_CLICK, self.on_show_popup_menu)
        mainSizer.Add(self._grid,1,wx.EXPAND|wx.ALL,5)

        mainPanel.SetSizer(mainSizer)

        self.SetSize((800,400))

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def build_menu(self):

        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        saveItem   = fileMenu.Append(wx.ID_ANY, '&Save database\tCtrl+S')
        saveasItem = fileMenu.Append(wx.ID_ANY, '&Save database as ...\tCtrl+Shift+S')
        menubar.Append(fileMenu, "File")

        databaseMenu = wx.Menu()
        addElementItem = databaseMenu.Append(wx.ID_ANY, 'New element')
        addPropertyItem = databaseMenu.Append(wx.ID_ANY, 'New property')
        menubar.Append(databaseMenu, "Database")

        self.Bind(wx.EVT_MENU,self.on_add_element, addElementItem)
        self.Bind(wx.EVT_MENU,self.on_add_property, addPropertyItem)

        self.Bind(wx.EVT_MENU,self.on_save_database, saveItem)
        self.Bind(wx.EVT_MENU,self.on_saveas_database, saveasItem)

        self.SetMenuBar(menubar)

    def on_show_popup_menu(self, event):

        menu = wx.Menu()

        saveItem = menu.Append(wx.ID_ANY, 'Save database')
        saveasItem = menu.Append(wx.ID_ANY, 'Save database as ...')
        menu.AppendSeparator()

        addElementItem = menu.Append(wx.ID_ANY, 'New element')
        addPropertyItem = menu.Append(wx.ID_ANY, 'New property')

        self.Bind(wx.EVT_MENU,self.on_add_element,addElementItem)
        self.Bind(wx.EVT_MENU,self.on_add_property,addPropertyItem)

        self.Bind(wx.EVT_MENU,self.on_save_database, saveItem)
        self.Bind(wx.EVT_MENU,self.on_saveas_database, saveasItem)

        self.PopupMenu(menu)

        menu.Destroy()

    def on_close(self,event):

        d = wx.MessageDialog(None, 'This will close the database editor. Continue ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_WARNING)

        if d.ShowModal() == wx.ID_NO:
            return

        self.Destroy()

    def on_edit_cell(self,event):

        event.Skip()

        self._grid.Refresh()

    def on_add_element(self, event):
        """
        Handler called when the user add new elements to the database.
        """

        d = NewElementDialog(self,title="Add element",size=(400,220))

        # If the new element dialog is closed by clicking on OK. 
        if d.ShowModal() == wx.ID_CANCEL:
            return

        # Get rid of wxpython unicode string formatting
        entry,name,symbol,mass = d.GetValue()

        self._database.add_row(entry,name,symbol,mass)

    def on_add_property(self, message):
        """
        Handler called when the user add a property to the database.
        """

        d = NewPropertyDialog(self,title="Add property")

        if d.ShowModal() == wx.ID_CANCEL:
            return

        pname,pdefault = d.GetValue()

        if not pname:
            return

        # Get rid of wxpython unicode string formatting
        pname = str(pname)

        self._database.add_column(pname,pdefault)

    def on_save_database(self,event=None):
        """
        Handler called when the user saves the database to its defaut location.
        """

        d = wx.MessageDialog(None, 'This will overwrite your database. Continue ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_WARNING)

        if d.ShowModal() == wx.ID_NO:
            return

        self._database.save()

    def on_saveas_database(self,event=None):
        """
        Handler called when the user saves the database to any location.
        """

        d = wx.FileDialog(self,
                          message="Save database as ...",
                          defaultDir=os.getcwd(),
                          defaultFile="elements_database",
                          wildcard="XML file (*.xml)|*.xml|CSV file (*.csv)|*.csv",
                          style=wx.SAVE|wx.FD_OVERWRITE_PROMPT)

        if d.ShowModal() == wx.ID_CANCEL:
            return

        filename = str(d.GetPath())

        if d.GetFilterIndex() == 0:
            fmt = 'xml'

        elif d.GetFilterIndex() == 1:
            fmt = 'csv'

        self._database.saveas(fmt,filename)

if __name__ == "__main__":
    app = wx.App(False)
    f = ElementsDatabaseEditor(None)
    f.Show()
    app.MainLoop()
