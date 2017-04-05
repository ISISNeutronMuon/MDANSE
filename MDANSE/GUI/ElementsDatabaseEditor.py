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
Created on Apr 14, 2015

:author: Eric C. Pellegrini
'''

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
        
        staticLabel0 = wx.StaticText(panel, -1, "Enter element settings")
        
        subPanel = wx.Panel(panel,wx.ID_ANY)
        staticLabel1 = wx.StaticText(subPanel, wx.ID_ANY, "Entry name")
        self._entry = wx.TextCtrl(subPanel, wx.ID_ANY)        
        staticLabel2 = wx.StaticText(subPanel, wx.ID_ANY, "Atom name")
        self._name = wx.TextCtrl(subPanel, id = wx.ID_ANY)
        staticLabel3 = wx.StaticText(subPanel, wx.ID_ANY, "Atom symbol")
        self._symbol = wx.TextCtrl(subPanel, wx.ID_ANY)        
        staticLabel4 = wx.StaticText(subPanel, wx.ID_ANY, "Atom Mass (uma)")
        self._mass = wx.TextCtrl(subPanel, id = wx.ID_ANY)
        
        staticLine = wx.StaticLine(self, wx.ID_ANY)

        buttonPanel = wx.Panel(self,wx.ID_ANY)
        ok = wx.Button(buttonPanel, wx.ID_OK, "OK")
        ok.SetDefault()
        cancel = wx.Button(buttonPanel, wx.ID_CANCEL, "Cancel")

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(staticLabel0, 0, wx.ALL|wx.ALIGN_LEFT, 5)
        subsizer = wx.GridBagSizer(5,5)
        subsizer.AddGrowableCol(1)
        subsizer.Add(staticLabel1,pos=(0,0),flag=wx.ALIGN_CENTER_VERTICAL)
        subsizer.Add(self._entry   ,pos=(0,1),flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subsizer.Add(staticLabel2,pos=(1,0),flag=wx.ALIGN_CENTER_VERTICAL)
        subsizer.Add(self._name,pos=(1,1),flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subsizer.Add(staticLabel3,pos=(2,0),flag=wx.ALIGN_CENTER_VERTICAL)
        subsizer.Add(self._symbol,pos=(2,1),flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subsizer.Add(staticLabel4,pos=(3,0),flag=wx.ALIGN_CENTER_VERTICAL)
        subsizer.Add(self._mass,pos=(3,1),flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subPanel.SetSizer(subsizer)
        panelSizer.Add(subPanel, 0, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(panelSizer)

        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(cancel)
        btnsizer.AddButton(ok)
        btnsizer.Realize()        
        buttonPanel.SetSizer(btnsizer)

        dlgsizer = wx.BoxSizer(wx.VERTICAL)
        dlgsizer.Add(panel, 1, wx.ALL|wx.EXPAND, 5)
        dlgsizer.Add(staticLine, 0, wx.ALL|wx.EXPAND, 5)
        dlgsizer.Add(buttonPanel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.EXPAND, 5)
        
        # Bind the top sizer to the dialog.
        self.SetSizer(dlgsizer)
                          
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
        
        staticLabel0 = wx.StaticText(panel, -1, "Enter property settings")
        
        subPanel = wx.Panel(panel,wx.ID_ANY)
        staticLabel1 = wx.StaticText(subPanel, wx.ID_ANY, "Name")
        self.name = wx.TextCtrl(subPanel, wx.ID_ANY)        
        staticLabel2 = wx.StaticText(subPanel, wx.ID_ANY, "Numeric type")
        self.propertyType = wx.ComboBox(subPanel, id = wx.ID_ANY, choices=ELEMENTS._TYPES.keys(), style=wx.CB_READONLY)
        
        staticLine = wx.StaticLine(self, wx.ID_ANY)

        buttonPanel = wx.Panel(self,wx.ID_ANY)
        ok = wx.Button(buttonPanel, wx.ID_OK, "OK")
        ok.SetDefault()
        cancel = wx.Button(buttonPanel, wx.ID_CANCEL, "Cancel")

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(staticLabel0, 0, wx.ALL|wx.ALIGN_LEFT, 5)
        subsizer = wx.GridBagSizer(5,5)
        subsizer.AddGrowableCol(1)
        subsizer.Add(staticLabel1,pos=(0,0),flag=wx.ALIGN_CENTER_VERTICAL)
        subsizer.Add(self.name   ,pos=(0,1),flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subsizer.Add(staticLabel2,pos=(1,0),flag=wx.ALIGN_CENTER_VERTICAL)
        subsizer.Add(self.propertyType,pos=(1,1),flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subPanel.SetSizer(subsizer)
        panelSizer.Add(subPanel, 0, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(panelSizer)

        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(cancel)
        btnsizer.AddButton(ok)
        btnsizer.Realize()        
        buttonPanel.SetSizer(btnsizer)

        dlgsizer = wx.BoxSizer(wx.VERTICAL)
        dlgsizer.Add(panel, 1, wx.ALL|wx.EXPAND, 5)
        dlgsizer.Add(staticLine, 0, wx.ALL|wx.EXPAND, 5)
        dlgsizer.Add(buttonPanel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.EXPAND, 5)
        
        # Bind the top sizer to the dialog.
        self.SetSizer(dlgsizer)
                          
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
 
        d = NewPropertyDialog(self,title="Add property",size=(400,160))
 
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