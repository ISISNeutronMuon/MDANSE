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

@author: Eric C. pellegrini
'''

import ast
import os

import wx
import wx.aui as wxaui
import wx.grid as wxgrid
import wx.lib.fancytext as wxfancytext
import wx.lib.stattext as wxstattext 

from MDANSE import ELEMENTS
from MDANSE.Core.Singleton import Singleton
from MDANSE.Externals.pubsub import pub

from MDANSE.App.GUI.Framework.Plugins.ComponentPlugin import ComponentPlugin

_LAYOUT = {} 
_LAYOUT["H"]   = (0,1) 
_LAYOUT["He"]  = (0,18)

_LAYOUT["Li"]  = (1,1)
_LAYOUT["Be"]  = (1,2)
_LAYOUT["B"]   = (1,13)
_LAYOUT["C"]   = (1,14)
_LAYOUT["N"]   = (1,15)
_LAYOUT["O"]   = (1,16)
_LAYOUT["F"]   = (1,17)
_LAYOUT["Ne"]  = (1,18)

_LAYOUT["Na"]  = (2,1)
_LAYOUT["Mg"]  = (2,2)
_LAYOUT["Al"]  = (2,13)
_LAYOUT["Si"]  = (2,14)
_LAYOUT["P"]   = (2,15)
_LAYOUT["S"]   = (2,16)
_LAYOUT["Cl"]  = (2,17)
_LAYOUT["Ar"]  = (2,18)

_LAYOUT["K"]   = (3,1)
_LAYOUT["Ca"]  = (3,2)
_LAYOUT["Sc"]  = (3,3)
_LAYOUT["Ti"]  = (3,4)
_LAYOUT["V"]   = (3,5)
_LAYOUT["Cr"]  = (3,6)
_LAYOUT["Mn"]  = (3,7)
_LAYOUT["Fe"]  = (3,8)
_LAYOUT["Co"]  = (3,9)
_LAYOUT["Ni"]  = (3,10)
_LAYOUT["Cu"]  = (3,11)
_LAYOUT["Zn"]  = (3,12)
_LAYOUT["Ga"]  = (3,13)
_LAYOUT["Ge"]  = (3,14)
_LAYOUT["As"]  = (3,15)
_LAYOUT["Se"]  = (3,16)
_LAYOUT["Br"]  = (3,17)
_LAYOUT["Kr"]  = (3,18)

_LAYOUT["Rb"]  = (4,1)
_LAYOUT["Sr"]  = (4,2)
_LAYOUT["Y"]   = (4,3)
_LAYOUT["Zr"]  = (4,4)
_LAYOUT["Nb"]  = (4,5)
_LAYOUT["Mo"]  = (4,6)
_LAYOUT["Tc"]  = (4,7)
_LAYOUT["Ru"]  = (4,8)
_LAYOUT["Rh"]  = (4,9)
_LAYOUT["Pd"]  = (4,10)
_LAYOUT["Ag"]  = (4,11)
_LAYOUT["Cd"]  = (4,12)
_LAYOUT["In"]  = (4,13)
_LAYOUT["Sn"]  = (4,14)
_LAYOUT["Sb"]  = (4,15)
_LAYOUT["Te"]  = (4,16)
_LAYOUT["I"]   = (4,17)
_LAYOUT["Xe"]  = (4,18)

_LAYOUT["Cs"]  = (5,1)
_LAYOUT["Ba"]  = (5,2)
_LAYOUT["Hf"]  = (5,4)
_LAYOUT["Ta"]  = (5,5)
_LAYOUT["W"]   = (5,6)
_LAYOUT["Re"]  = (5,7)
_LAYOUT["Os"]  = (5,8)
_LAYOUT["Ir"]  = (5,9)
_LAYOUT["Pt"]  = (5,10)
_LAYOUT["Au"]  = (5,11)
_LAYOUT["Hg"]  = (5,12)
_LAYOUT["Tl"]  = (5,13)
_LAYOUT["Pb"]  = (5,14)
_LAYOUT["Bi"]  = (5,15)
_LAYOUT["Po"]  = (5,16)
_LAYOUT["At"]  = (5,17)
_LAYOUT["Rn"]  = (5,18)

_LAYOUT["Fr"]  = (6,1)
_LAYOUT["Ra"]  = (6,2)
_LAYOUT["Rf"]  = (6,4)
_LAYOUT["Db"]  = (6,5)
_LAYOUT["Sg"]  = (6,6)
_LAYOUT["Bh"]  = (6,7)
_LAYOUT["Hs"]  = (6,8)
_LAYOUT["Mt"]  = (6,9)
_LAYOUT["Ds"]  = (6,10)
_LAYOUT["Rg"]  = (6,11)
_LAYOUT["Cn"]  = (6,12)
_LAYOUT["Uut"] = (6,13)
_LAYOUT["Fl"]  = (6,14)
_LAYOUT["Uup"] = (6,15)
_LAYOUT["Lv"]  = (6,16)
_LAYOUT["Uus"] = (6,17)
_LAYOUT["Uuo"] = (6,18)

_LAYOUT["La"]  = (8,4)
_LAYOUT["Ce"]  = (8,5)
_LAYOUT["Pr"]  = (8,6)
_LAYOUT["Nd"]  = (8,7)
_LAYOUT["Pm"]  = (8,8)
_LAYOUT["Sm"]  = (8,9)
_LAYOUT["Eu"]  = (8,10)
_LAYOUT["Gd"]  = (8,11)
_LAYOUT["Tb"]  = (8,12)
_LAYOUT["Dy"]  = (8,13)
_LAYOUT["Ho"]  = (8,14)
_LAYOUT["Er"]  = (8,15)
_LAYOUT["Tm"]  = (8,16)
_LAYOUT["Yb"]  = (8,17)
_LAYOUT["Lu"]  = (8,18)

_LAYOUT["Ac"]  = (9,4)
_LAYOUT["Th"]  = (9,5)
_LAYOUT["Pa"]  = (9,6)
_LAYOUT["U"]   = (9,7)
_LAYOUT["Np"]  = (9,8)
_LAYOUT["Pu"]  = (9,9)
_LAYOUT["Am"]  = (9,10)
_LAYOUT["Cm"]  = (9,11)
_LAYOUT["Bk"]  = (9,12)
_LAYOUT["Cf"]  = (9,13)
_LAYOUT["Es"]  = (9,14)
_LAYOUT["Fm"]  = (9,15)
_LAYOUT["Md"]  = (9,16)
_LAYOUT["No"]  = (9,17)
_LAYOUT["Lr"]  = (9,18)

_COLS = range(1,19)
_ROWS = ["i","ii","iii","iv","v","vi","vii"]

# Dictionary that maps the chemical family with a RGB color.
_FAMILY = {'default' : (128, 128, 128),
           'user-defined' : (255, 255, 255),
           'non metal' : (153, 255, 153),
           'noble gas' : (192, 255, 255),
           'alkali metal' : (255, 153, 153),
           'alkaline earth metal' : (255, 222, 173),
           'metalloid' : (204, 204, 153),
           'halogen' : (255, 255, 153),
           'post-transition metal' : (204, 204, 204),
           'transition metal' : (255, 192, 192),
           'lanthanoid' : (255, 191, 255),
           'actinoid' : (255, 153, 294)}
    
# Dictionary that maps the chemical state with a RGB color.
_STATE = {'default' : (128, 128, 128),
          'user-defined' : (255,0,0),
          'gas' : (255,0,0),
          'liquid' : (0,0,255),
          'solid' : (0,0,0),
          'unknown' : (0,150,0)}

class PropertyDialog(wx.Dialog):
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
        staticLabel2 = wx.StaticText(subPanel, wx.ID_ANY, "Default value")
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
        
        # Layout the widget.
        self.Layout()
          
    def GetValue(self, event=None):
        """
        Handler called when the user clicks on the OK button of the property dialog.
        """
        
        pname = str(self.name.GetValue().strip())
        
        pdefault = str(self.propertyType.GetValue())
                                
        return pname,pdefault

class StaticFancyText(wxfancytext.StaticFancyText):
    """
    StaticFancyText with SetLabel function.
    """

    def SetLabel(self, label):
        """
        Overload of the StaticFancyText.SetLabel method
        """
                
        bmp = wxfancytext.RenderToBitmap(label, wx.Brush(self.GetParent().GetBackgroundColour(), wx.SOLID))
        
        self.SetBitmap(bmp)

class ElementInfoPanel(wx.Panel):
    """
    This class creates a panel that contains all the information stored in the database about a given element.
    """

    def __init__(self, parent, element, *args,**kwds):
        """
        The constructor.

        :Parameters:
            #. parent  (wx window): the parent window.
            #. element (string): the element name.
        """
        
        # The base class constructor.        
        wx.Panel.__init__(self, parent, *args, **kwds)
        
        # The main panel sizer.        
        sizer = wx.BoxSizer(wx.VERTICAL)
                        
        # A text widget is created to display the information about the selected element.
        text = wx.StaticText(self,wx.ID_ANY,label=ELEMENTS.info(element))

        # The background color of the text widget is set.
        self.SetBackgroundColour(wx.Colour(255,236,139))

        # The font of the text widget is set.        
        text.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # The text widget is added to the main panel sizer.
        sizer.Add(text, 1, wx.ALL|wx.EXPAND, 5)
        
        # An hyperlink widget is created for opening the url about the selected element.
        hyperlink = wx.HyperlinkCtrl(self, wx.ID_ANY, label="More about %s" % ELEMENTS[element,'name'], url=ELEMENTS[element,'url'])
        # The hyperlink widget is added to the main panel sizer.
        sizer.Add(hyperlink, 0, wx.ALL|wx.EXPAND, 5)
        
        # The main panel sizer is set and fitted with its contents.
        self.SetSizer(sizer)
        # The frame is fitted with its contents.        
        sizer.Fit(self)
        
        self.Layout()
        
class ElementShortInfoPanel(wx.Panel):
    """
    This class creates a panel that displays a summary of the information stored in the database for a given element.
    """

    def __init__(self, parent, element="H"):
        """
        The constructor.

        :Parameters:
            #. parent  (wx window): the parent window.
            #. element (string): the element name.
        """

        # The base class constructor.                
        wx.Panel.__init__(self, parent=parent, style=wx.BORDER_SUNKEN)
                
        # This will store the name of the element for which the summary is currently displayed. 
        self.selected = None

        # The top sizer that will arrange the summary widget as a grid.
        self.sizer = wx.GridBagSizer(0,0)
        self.sizer.SetEmptyCellSize((20,20))

        # The static texts that will display the informations about a given element.
        self.family = wx.StaticText(self, label="", style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE|wx.EXPAND)
        self.family.SetToolTipString("Chemical family")        
        self.family.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD))

        # The element symbol.
        self.symbol = wx.StaticText(self, label="",style=wx.ALIGN_LEFT|wx.ST_NO_AUTORESIZE)        
        self.symbol.SetToolTipString("Symbol")        
        self.symbol.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        # The element atomic number.
        self.z = wx.StaticText(self, label="", style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE|wx.EXPAND)
        self.z.SetToolTipString("Atomic number")
        self.z.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        # The element position in the periodic table.
        self.position = wx.StaticText(self, label="", size=(40,15), style=wx.ALIGN_CENTER_VERTICAL|wx.ST_NO_AUTORESIZE)        
        self.position.SetToolTipString("Group,Period,Block")
        self.position.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                
        # The element full name.
        self.atom = wx.StaticText(self, label="" , style=wx.ALIGN_CENTER|wx.ST_NO_AUTORESIZE)        
        self.atom.SetToolTipString("Atom")
        self.atom.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
                
        # The element electronic configuration.
        self.configuration = StaticFancyText(self, wx.ID_ANY, "", style=wx.EXPAND|wx.ALIGN_LEFT|wx.ST_NO_AUTORESIZE)
        self.configuration.SetToolTipString("Electron configuration")
        
        # The element atomic weight.
        self.atomicWeight = wx.StaticText(self, label="", style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.atomicWeight.SetToolTipString("Relative atomic mass (uma)")
       
        # The element electronegativity.
        self.electroNegativity = wx.StaticText(self, label="", style=wx.EXPAND|wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.electroNegativity.SetToolTipString("Electronegativity")
        
        # The element electroaffinity.
        self.electroAffinity = wx.StaticText(self, label="", style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)        
        self.electroAffinity.SetToolTipString("Electroaffinity (eV)")
        
        # The element ionization energy.
        self.ionizationEnergy = wx.StaticText(self, label="", style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)        
        self.ionizationEnergy.SetToolTipString("Ionization energy (eV)")

        # The widgets are placed into the gridbag top sizer.
        self.sizer.Add(self.family           , pos=(0,1), span=(1,16), flag=wx.EXPAND)
        self.sizer.Add(self.z                , pos=(1,0), span=(1,3) , flag=wx.EXPAND)
        self.sizer.Add(self.position         , pos=(6,0), span=(1,6) , flag=wx.EXPAND)
        self.sizer.Add(self.symbol           , pos=(2,2), span=(2,7) , flag=wx.EXPAND)
        self.sizer.Add(self.configuration    , pos=(2,10), span=(2,8), flag=wx.EXPAND)
        self.sizer.Add(self.atom             , pos=(4,0), span=(1,7) , flag=wx.EXPAND)
        self.sizer.Add(self.atomicWeight     , pos=(4,14), span=(1,3), flag=wx.EXPAND)
        self.sizer.Add(self.electroNegativity, pos=(5,14), span=(1,3), flag=wx.EXPAND)
        self.sizer.Add(self.electroAffinity  , pos=(6,14), span=(1,3), flag=wx.EXPAND)
        self.sizer.Add(self.ionizationEnergy , pos=(7,14), span=(1,3), flag=wx.EXPAND)

        # The main panel sizer is set and fitted with its contents.
        self.SetSizer(self.sizer)
        
        # The frame is fitted with its contents.        
        self.sizer.Fit(self)
        
        self.Layout()
        
        # The selected element is set.
        self.set_selection(element)
        
        
    def set_selection(self, element):               
        """
        Select an element whose summary will be displayed..

        :Parameters:
            #. element (string): the element name.
        """

        # If the element is already the one displayed, just return.        
        if self.selected == element:
            return

        # The new element becomes the current one.
        self.selected = element
        
        # Prevents any updates from taking place on screen.
        self.Freeze()
                
        # The element database instance.
        element = ELEMENTS.get_element(element)
        
        # Its chemical family.
        family = element['family']
        color = _FAMILY.get(family,_FAMILY['default'])

        # Change the main panel background color according to the element chemical family.        
        self.SetBackgroundColour((color[0], color[1], color[2]))
                        
        # Updates the different static text according to the new element properties.
        self.family.SetLabel("%s " % family)
        self.symbol.SetLabel(element['symbol'])
        self.z.SetLabel("%4s" % element['proton'])
        self.position.SetLabel("%2s,%s,%s" % (element['group'], element['period'], element['block']))
        self.atom.SetLabel(element['name'])
        self.atomicWeight.SetLabel("%s" % element['atomic_weight'])
        self.electroNegativity.SetLabel("%s" % element['electronegativity'])
        self.electroAffinity.SetLabel("%s" % element['electroaffinity'])
        self.ionizationEnergy.SetLabel("%s" % element['ionization_energy'])

        label = []
        for orb in element['configuration'].split():
            if not orb.startswith('[') and len(orb) > 2:
                orb = orb[:2] + '<sup>' + orb[2:] + '</sup>'
            label.append(orb)
        label.append("<sup> </sup>")
        self.configuration.SetLabel(' '.join(label))

        # Reenables the main panel updating after the previous call to Freeze.
        self.Thaw()
 
                            
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
    
    def add_row(self, ename):
                                
        ELEMENTS.add_element(ename)
                                        
        self.notify_grid(wxgrid.GRIDTABLE_NOTIFY_ROWS_APPENDED, 1)
        
    def notify_grid(self, msg, count):
        "Notifies the grid of the message and the affected count."
        
        tbl_msg = wxgrid.GridTableMessage(self, msg, count)                      
         
        self.GetView().ProcessTableMessage(tbl_msg)
        
    def saveas(self,fmt,filename):
        
        ELEMENTS.export(fmt,filename)
        
    def save(self, fmt="csv", filename=None):
        
        ELEMENTS.save()                    

class DatabasePanel(wx.Panel):
    
    def __init__(self, parent, database):
        """
        The constructor.
        :Parameters:
            #. parent  (wx window): the parent window.
        """
                
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self._parent = parent
        
        self._database = database
        
        self.build_panel()
        
    
    def build_panel(self):
        
        boxsizer = wx.BoxSizer(wx.VERTICAL)
  
        # The wx grid that will store the database.            
        self.grid = wxgrid.Grid(self)
  
        # The grid style is set. This will be a standard text editor.
        self.grid.SetDefaultEditor(wxgrid.GridCellTextEditor())
                                                    
        self.grid.SetTable(self._database)
          
        self.grid.SetDefaultCellBackgroundColour(wx.NamedColour("LIGHT BLUE"))
          
        self.grid.SetColLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
          
        self.grid.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
  
        self.grid.SetColMinimalAcceptableWidth(100)
          
        self.grid.Bind(wxgrid.EVT_GRID_CELL_CHANGE,self.on_edit_cell)
        self.grid.Bind(wxgrid.EVT_GRID_CELL_RIGHT_CLICK, self.on_show_popup_menu)
        boxsizer.Add(self.grid,1,wx.EXPAND|wx.ALL,5)
                                        
        self.SetSizer(boxsizer)
        boxsizer.Fit(self)
        self.Layout()    
        
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_show_popup_menu)
        
    def on_show_popup_menu(self, event):

        menu = wx.Menu()

        saveItem = menu.Append(wx.ID_ANY, 'Save database')
        saveasItem = menu.Append(wx.ID_ANY, 'Save database as ...')        
        menu.AppendSeparator()

        addElementItem = menu.Append(wx.ID_ANY, 'New element')
        addPropertyItem = menu.Append(wx.ID_ANY, 'New property')

        self.Bind(wx.EVT_MENU,self._parent.on_add_element,addElementItem)
        self.Bind(wx.EVT_MENU,self._parent.on_add_property,addPropertyItem)

        self.Bind(wx.EVT_MENU,self._parent.on_save_database, saveItem)
        self.Bind(wx.EVT_MENU,self._parent.on_saveas_database, saveasItem)

        self.PopupMenu(menu)

        menu.Destroy()
                        
    def on_edit_cell(self,event):
        
        event.Skip()
        
        self.grid.Refresh()
        
class PeriodicTablePanel(wx.Panel):
    """
    This class creates a panel that will display the periodic table. Each element of the periodic table is a button
    that when clicked on will list the natural element and the different isotopes found in the database for the 
    selected element. There is also a special button that when clicked will display the "user-defined elements".
    """                 
                         
    def __init__(self, parent):
        """
        The constructor.
        :Parameters:
            #. parent  (wx window): the parent window.
        """
                
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self._parent = parent
        self.build_panel()
    
    def build_panel(self):
        
        # The top sizer that will contains all the periodic table widgets.                                    
        general_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(0,0)
        sizer.SetEmptyCellSize((20,20))

        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)) 
        
        for i in _COLS:
            wid = wxstattext.GenStaticText(parent =self,ID = wx.ID_ANY, label=str(i), size=(40,40), style = wx.ALIGN_CENTRE|wx.EXPAND)   
            sizer.Add(wid, (0,i), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        for i,v in enumerate(_ROWS):
            wid = wxstattext.GenStaticText(parent =self,ID = wx.ID_ANY, label=v, size=(40,40), style = wx.ALIGN_CENTRE|wx.EXPAND)   
            sizer.Add(wid, (i+1,0), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        wid = wxstattext.GenStaticText(parent =self,ID = wx.ID_ANY, label="*", size=(40,40), style = wx.ALIGN_CENTRE|wx.EXPAND)   
        sizer.Add(wid, (6,3), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        wid = wxstattext.GenStaticText(parent =self,ID = wx.ID_ANY, label="**", size=(40,40), style = wx.ALIGN_CENTRE|wx.EXPAND)   
        sizer.Add(wid, (7,3), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        wid = wxstattext.GenStaticText(parent =self,ID = wx.ID_ANY, label="*", size=(40,40), style = wx.ALIGN_CENTRE|wx.EXPAND)   
        sizer.Add(wid, (9,3), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        wid = wxstattext.GenStaticText(parent =self,ID = wx.ID_ANY, label="**", size=(40,40), style = wx.ALIGN_CENTRE|wx.EXPAND)   
        sizer.Add(wid, (10,3), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        # The panel that will contain the short info about a selected element.
        self.shortInfo = ElementShortInfoPanel(self)
        sizer.Add(self.shortInfo, (1,5), (3,6), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        symbs = []
        for el in ELEMENTS.elements:
            info = ELEMENTS.get_element(el)
            if info['symbol'] in symbs:
                continue
            symbs.append(info['symbol'])
            try:
                r,c = _LAYOUT[info['symbol']]
                wid = wxstattext.GenStaticText(parent =self,ID = wx.ID_ANY, label=info["symbol"], size=(40,40), style = wx.ALIGN_CENTRE|wx.EXPAND)
                wid.SetToolTipString(info['name'])
                bkg_color = _FAMILY[info['family']]
                wid.SetBackgroundColour((bkg_color[0], bkg_color[1], bkg_color[2]))
                fg_color = _STATE[info['state']]
                wid.SetForegroundColour((fg_color[0], fg_color[1], fg_color[2]))                                            
                wid.Bind(wx.EVT_LEFT_DOWN, self.on_select_element)
                wid.Bind(wx.EVT_ENTER_WINDOW, self.on_display_element_short_info)
                sizer.Add(wid, (r+1,c), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)
            except KeyError:
                continue
                    
        general_sizer.Add(sizer,0,wx.ALL|wx.EXPAND,5)
        
        self.SetSizer(general_sizer)
        general_sizer.Fit(self)
        self.Layout()
                                    
    def on_quit(self, event):

        d = wx.MessageDialog(None,
                             'Do you really want to quit the database editor ?',
                             'Question',
                             wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()

                
    def on_select_element(self, event=None):
                
        # The button of the periodic table that was clicked on.
        button = event.GetEventObject()
        
        element = button.GetLabel()
        
        siz = button.GetSize()
        
        pos = button.GetPosition()
                                                            
        # A menu is created.
        menu = wx.Menu()
        
        # The natural element and its different isotopes are appended to the menu.
        for iso in ELEMENTS.get_isotopes(element):
            item = menu.Append(wx.ID_ANY, iso)
            menu.Bind(wx.EVT_MENU, self.on_display_element_info, item)            

        self.PopupMenu(menu, wx.Point(pos.x, pos.y+siz.y))
                
        menu.Destroy()

    def display_element_short_info(self, element):
                                      
        self.shortInfo.set_selection(element)
                
    def on_display_element_short_info(self, event=None):

        element = event.GetEventObject().GetLabel()
            
        self.display_element_short_info(element)
        
    def on_display_element_info(self, event=None):
                
        # The button of the periodic table that was clicked on.
        wid = event.GetEventObject()
        
        if isinstance(wid,wx.Menu):
            # The entry that was selected.
            element = wid.FindItemById(event.GetId()).GetText()
        else:
            element = wid.GetValue()
                                                     
        # Pops up the information dialog about the selected isotope.
        elementPanel = ElementInfoPanel(self, element)
        self._parent._mgr.AddPane(elementPanel, wxaui.AuiPaneInfo().Dockable(False).Float().CloseButton(True).DestroyOnClose(True)) 
        self._parent._mgr.Update() 
      

class PeriodicTablePlugin(ComponentPlugin):

    type = "periodic_table"
    
    label = "Periodic Table"
    
    ancestor = None

    def build_panel(self):
        
        self._database = Database()
                
        self._databasePanel = DatabasePanel(self, self._database)
        self._periodicTablePanel = PeriodicTablePanel(self)
        
        self._mgr.AddPane(self._databasePanel, wxaui.AuiPaneInfo().Dock().Center().CloseButton(False))  
        self._mgr.AddPane(self._periodicTablePanel, wxaui.AuiPaneInfo().Float().Dockable().CloseButton(False))
            
        self._mgr.Update()
              
    @property
    def periodictablePanel(self):
        return self._periodicTablePanel
               
    @property
    def databasePanel(self):
        return self._databasePanel
    
    def plug(self, *args, **kwargs):

        self._parent._mgr.GetPane(self).Dock().Floatable(False).Center().CloseButton(True).Caption("Periodic table")
        self._parent._mgr.Update()                   
            
    def on_add_element(self, message):
        """
        Handler called when the user add new elements to the database.
        """

        d = wx.TextEntryDialog(self,"Enter element id","add element")

        # If the new element dialog is closed by clicking on OK. 
        if d.ShowModal() == wx.ID_CANCEL:
            return

        ename = d.GetValue()
                        
        if not ename:
            return
                                
        self._database.add_row(ename)
        
    def on_add_property(self, message):
        """
        Handler called when the user add a property to the database.
        """

        d = PropertyDialog(self,title="Add property",size=(400,160))

        if d.ShowModal() == wx.ID_CANCEL:
            return

        pname,pdefault = d.GetValue()
                    
        if not pname:
            return    
                                    
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
            
class PeriodicTableFrame(wx.Frame):
    
    def __init__(self, parent, title="Periodic table"):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)

        self.build_dialog()
        
        self.build_menu()

    def build_menu(self):

        menubar = wx.MenuBar()
        
        fileMenu = wx.Menu()
        
        saveItem   = fileMenu.Append(wx.ID_ANY, '&Save database\tCtrl+S')
        saveasItem = fileMenu.Append(wx.ID_ANY, '&Save database as ...\tCtrl+Shift+S')        
        fileMenu.AppendSeparator()
        fileItem = fileMenu.Append(wx.ID_ANY, '&Quit\tCtrl+Q')
        menubar.Append(fileMenu, "File")

        databaseMenu = wx.Menu()
        addElementItem = databaseMenu.Append(wx.ID_ANY, 'New element')
        addPropertyItem = databaseMenu.Append(wx.ID_ANY, 'New property')
        menubar.Append(databaseMenu, "Database")
                
        self.Bind(wx.EVT_CLOSE,self.on_quit)
        self.Bind(wx.EVT_MENU,self.on_quit,fileItem)

        self.Bind(wx.EVT_MENU,self._periodicTablePlugin.on_add_element, addElementItem)
        self.Bind(wx.EVT_MENU,self._periodicTablePlugin.on_add_property, addPropertyItem)

        self.Bind(wx.EVT_MENU,self._periodicTablePlugin.on_save_database, saveItem)
        self.Bind(wx.EVT_MENU,self._periodicTablePlugin.on_saveas_database, saveasItem)

        self.SetMenuBar(menubar)
       
    def build_dialog(self):
        
        mainPanel = wx.Panel(self, wx.ID_ANY)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self._periodicTablePlugin = PeriodicTablePlugin(mainPanel)
        
        mainSizer.Add(self._periodicTablePlugin, 1, wx.ALL|wx.EXPAND, 5)

        mainPanel.SetSizer(mainSizer)        
        mainSizer.Fit(mainPanel)
        mainPanel.Layout()

        self.SetSize((900, 600))

    def on_quit(self, event):
        
        d = wx.MessageDialog(None,
                             'Do you really want to quit ?',
                             'Question',
                             wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()   

if __name__ == "__main__":
    app = wx.App(False)
    f = PeriodicTableFrame(None)
    f.Show()
    app.MainLoop()    