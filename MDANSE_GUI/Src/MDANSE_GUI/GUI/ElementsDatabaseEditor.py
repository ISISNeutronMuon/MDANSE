# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/ElementsDatabaseEditor.py
# @brief     Implements module/class/test ElementsDatabaseEditor
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx
import wx.grid as wxgrid

from MDANSE import PLATFORM
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton


class ElementsDatabaseError(Error):
    pass


class NewElementDialog(wx.Dialog):
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

        panel = wx.Panel(self, wx.ID_ANY)

        # Create text and answer box widgets
        staticLabel0 = wx.StaticText(panel, -1, "Enter element settings")
        staticLabel1 = wx.StaticText(panel, wx.ID_ANY, "Short name")
        self._entry = wx.TextCtrl(panel, wx.ID_ANY)
        staticLabel2 = wx.StaticText(panel, wx.ID_ANY, "Long name")
        self._element = wx.TextCtrl(panel, id=wx.ID_ANY)
        staticLabel3 = wx.StaticText(panel, wx.ID_ANY, "Symbol")
        self._symbol = wx.TextCtrl(panel, wx.ID_ANY)

        # Create buttons
        ok = wx.Button(panel, wx.ID_OK, "OK")
        ok.SetDefault()
        cancel = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        # Create main sizer and add the instruction text to the top
        main_sizer = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        main_sizer.Add(staticLabel0, 0, wx.ALL | wx.ALIGN_LEFT, 5)

        # Place the other text and answer box widgets in a grid
        body_sizer = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=20)
        body_sizer.Add(staticLabel1, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=10)
        body_sizer.Add(
            self._entry, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.EXPAND, border=10
        )
        body_sizer.Add(staticLabel2, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=10)
        body_sizer.Add(
            self._element,
            flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.EXPAND,
            border=10,
        )
        body_sizer.Add(staticLabel3, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=10)
        body_sizer.Add(
            self._symbol,
            flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.EXPAND,
            border=10,
        )
        main_sizer.Add(body_sizer, 0, wx.ALL | wx.EXPAND, 5)

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
        self.SetMinSize(wx.Size(400, 160))
        panel.SetSizerAndFit(main_sizer)
        self.Fit()

    def GetValue(self, event=None):
        """
        Handler called when the user clicks on the OK button of the property dialog.
        """

        entry = str(self._entry.GetValue().strip())
        if not entry:
            raise ElementsDatabaseError("Empty entry name")

        element = str(self._element.GetValue().strip())
        if not element:
            raise ElementsDatabaseError("Empty name")

        symbol = str(self._symbol.GetValue().strip())
        if not symbol:
            raise ElementsDatabaseError("Empty symbol")

        return entry, element, symbol


class NewPropertyDialog(wx.Dialog):
    """
    This class pops up a dialog that prompts the user for registering a new property in the database.
    """

    def __init__(self, *args, **kwargs):
        """
        The constructor.
        """

        # The base class constructor
        wx.Dialog.__init__(self, *args, **kwargs)

        self.Center()

        panel = wx.Panel(self, wx.ID_ANY)

        # Create text and answer box widgets
        staticLabel0 = wx.StaticText(panel, -1, "Enter property settings")
        staticLabel1 = wx.StaticText(panel, wx.ID_ANY, "Name")
        self.name = wx.TextCtrl(panel, wx.ID_ANY)
        staticLabel2 = wx.StaticText(panel, wx.ID_ANY, "Property type")
        self.propertyType = wx.ComboBox(
            panel,
            id=wx.ID_ANY,
            choices=list(ATOMS_DATABASE._TYPES.keys()),
            style=wx.CB_READONLY,
        )

        # Create button widgets
        cancel = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        ok = wx.Button(panel, wx.ID_OK, "OK")
        ok.SetDefault()

        # Create the main sizer and add the instruction
        main_sizer = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        main_sizer.Add(staticLabel0, 0, wx.ALL | wx.ALIGN_LEFT, 5)

        # Create sizer for the other texts and the answer boxes, and add the widets
        body_sizer = wx.FlexGridSizer(rows=2, cols=2, vgap=15, hgap=20)
        main_sizer.Add(body_sizer, flag=wx.EXPAND)
        body_sizer.Add(
            staticLabel1,
            flag=wx.ALIGN_LEFT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL,
            border=10,
        )
        body_sizer.Add(self.name, flag=wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT, border=10)
        body_sizer.Add(staticLabel2, flag=wx.ALIGN_LEFT | wx.LEFT, border=10)
        body_sizer.Add(
            self.propertyType, flag=wx.ALIGN_LEFT | wx.EXPAND | wx.RIGHT, border=10
        )

        # Button sizer and widgets
        button_sizer = wx.StdDialogButtonSizer()
        button_sizer.AddButton(cancel)
        button_sizer.AddButton(ok)
        button_sizer.Realize()
        main_sizer.Add(button_sizer, 0, wx.EXPAND)

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

        pclass = str(self.propertyType.GetValue())

        return pname, pclass


class Database(wxgrid.PyGridTableBase, metaclass=Singleton):
    def GetColLabelValue(self, col):
        return "%s" % ATOMS_DATABASE.properties[col]

    def GetNumberCols(self):
        return ATOMS_DATABASE.n_properties

    def GetNumberRows(self):
        return ATOMS_DATABASE.n_atoms

    def GetRowLabelValue(self, row):
        return ATOMS_DATABASE.atoms[row]

    def GetValue(self, row, col):
        atom = ATOMS_DATABASE.atoms[row]
        pname = ATOMS_DATABASE.properties[col]
        return ATOMS_DATABASE.get_value(atom, pname)

    def SetValue(self, row, col, val):
        atom = ATOMS_DATABASE.atoms[row]
        pname = ATOMS_DATABASE.properties[col]

        ATOMS_DATABASE.set_value(atom, pname, val)

    def add_column(self, pname, ptype):
        ATOMS_DATABASE.add_property(pname, ptype)

        self.notify_grid(wxgrid.GRIDTABLE_NOTIFY_COLS_APPENDED, 1)

    def add_row(self, entry, element, symbol):
        if ATOMS_DATABASE.has_atom(entry):
            return

        ATOMS_DATABASE.add_atom(entry)
        ATOMS_DATABASE.set_value(entry, "element", element)
        ATOMS_DATABASE.set_value(entry, "symbol", symbol)

        self.notify_grid(wxgrid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)

    def notify_grid(self, msg, count):
        """Notifies the grid of the message and the affected count."""

        tbl_msg = wxgrid.GridTableMessage(self, msg, count)

        self.GetView().ProcessTableMessage(tbl_msg)

    @staticmethod
    def save():
        ATOMS_DATABASE.save()


class ElementsDatabaseEditor(wx.Frame):
    def __init__(self, parent):
        """
        The constructor.
        :Parameters:
            #. parent  (wx window): the parent window.
        """

        wx.Frame.__init__(
            self,
            parent,
            wx.ID_ANY,
            title="Elements database editor",
            style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER,
        )

        self._database = Database()

        self.build_dialog()

        self.build_menu()

        self.CenterOnParent()

    def build_dialog(self):
        mainPanel = wx.Panel(self, wx.ID_ANY)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # The wx grid that will store the database.
        self._grid = wxgrid.Grid(mainPanel)

        # The grid style is set. This will be a standard text editor.
        self._grid.SetDefaultEditor(wxgrid.GridCellTextEditor())

        self._grid.SetTable(self._database)

        self._grid.SetDefaultCellBackgroundColour(wx.Colour("LIGHT BLUE"))

        self._grid.SetColLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

        self._grid.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        self._grid.SetColMinimalAcceptableWidth(100)

        self._grid.Bind(wxgrid.EVT_GRID_CELL_CHANGED, self.on_edit_cell)
        self._grid.Bind(wxgrid.EVT_GRID_CELL_RIGHT_CLICK, self.on_show_popup_menu)
        mainSizer.Add(self._grid, 1, wx.EXPAND | wx.ALL, 5)

        mainPanel.SetSizer(mainSizer)

        self.SetSize((800, 400))

        self.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def build_menu(self):
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        saveItem = fileMenu.Append(wx.ID_ANY, "&Save database\tCtrl+S")
        menubar.Append(fileMenu, "File")

        databaseMenu = wx.Menu()
        addElementItem = databaseMenu.Append(wx.ID_ANY, "New element")
        addPropertyItem = databaseMenu.Append(wx.ID_ANY, "New property")
        menubar.Append(databaseMenu, "Database")

        self.Bind(wx.EVT_MENU, self.on_add_element, addElementItem)
        self.Bind(wx.EVT_MENU, self.on_add_property, addPropertyItem)

        self.Bind(wx.EVT_MENU, self.on_save_database, saveItem)

        self.SetMenuBar(menubar)

    def on_show_popup_menu(self, event):
        menu = wx.Menu()

        saveItem = menu.Append(wx.ID_ANY, "Save database")
        menu.AppendSeparator()

        addElementItem = menu.Append(wx.ID_ANY, "New element")
        addPropertyItem = menu.Append(wx.ID_ANY, "New property")

        self.Bind(wx.EVT_MENU, self.on_add_element, addElementItem)
        self.Bind(wx.EVT_MENU, self.on_add_property, addPropertyItem)

        self.Bind(wx.EVT_MENU, self.on_save_database, saveItem)

        self.PopupMenu(menu)

        menu.Destroy()

    def on_close(self, event):
        d = wx.MessageDialog(
            None,
            "This will close the database editor. Continue ?",
            "Question",
            wx.YES_NO | wx.YES_DEFAULT | wx.ICON_WARNING,
        )

        if d.ShowModal() == wx.ID_NO:
            return

        self.Destroy()

    def on_edit_cell(self, event):
        event.Skip()

        self._grid.Refresh()

    def on_add_element(self, event):
        """
        Handler called when the user add new elements to the database.
        """

        d = NewElementDialog(self, title="Add element", size=(400, 220))

        # If the new element dialog is closed by clicking on OK.
        if d.ShowModal() == wx.ID_CANCEL:
            return

        # Get rid of wxpython unicode string formatting
        entry, element, symbol = d.GetValue()

        self._database.add_row(entry, element, symbol)

    def on_add_property(self, message):
        """
        Handler called when the user add a property to the database.
        """

        d = NewPropertyDialog(self, title="Add property")

        if d.ShowModal() == wx.ID_CANCEL:
            return

        pname, ptype = d.GetValue()

        if not pname:
            return

        # Get rid of wxpython unicode string formatting
        pname = str(pname)

        self._database.add_column(pname, ptype)

    def on_save_database(self, event=None):
        """
        Handler called when the user saves the database to its defaut location.
        """

        d = wx.MessageDialog(
            None,
            "This will overwrite your database. Continue ?",
            "Question",
            wx.YES_NO | wx.YES_DEFAULT | wx.ICON_WARNING,
        )

        if d.ShowModal() == wx.ID_NO:
            return

        self._database.save()


if __name__ == "__main__":
    app = wx.App(False)
    f = ElementsDatabaseEditor(None)
    f.Show()
    app.MainLoop()
