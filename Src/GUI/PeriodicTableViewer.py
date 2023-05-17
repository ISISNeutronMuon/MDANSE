# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/PeriodicTableViewer.py
# @brief     Implements module/class/test PeriodicTableViewer
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx
import wx.lib.fancytext as wxfancytext

from MDANSE import ELEMENTS
from MDANSE.GUI.ElementsDatabaseEditor import ElementsDatabaseEditor

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

_COLS = list(range(1,19))
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

class ElementInfoFrame(wx.Frame):
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
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Information about %s element" % element, style=wx.DEFAULT_FRAME_STYLE&~(wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER))
        
        # The main panel
        mainPanel = wx.Panel(self,wx.ID_ANY)
        
        # The main panel sizer.        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
                        
        # A text widget is created to display the information about the selected element.
        text = wx.StaticText(mainPanel,wx.ID_ANY,label=ELEMENTS.info(element))

        # The background color of the text widget is set.
        mainPanel.SetBackgroundColour(wx.Colour(255,236,139))
        info = ELEMENTS.get_element(element)
        bgColor = _FAMILY[info['family']]
        mainPanel.SetBackgroundColour(bgColor)

        # The font of the text widget is set.        
        text.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        
        # The text widget is added to the main panel sizer.
        mainSizer.Add(text, 1, wx.ALL|wx.EXPAND, 5)
        
        # An hyperlink widget is created for opening the url about the selected element.
        hyperlink = wx.HyperlinkCtrl(mainPanel, wx.ID_ANY, label="More about %s" % ELEMENTS[element,'name'], url=ELEMENTS[element,'url'])
        
        # The hyperlink widget is added to the main panel sizer.
        mainSizer.Add(hyperlink, 0, wx.ALL|wx.EXPAND, 5)
        
        # The main panel sizer is set and fitted with its contents.
        mainPanel.SetSizer(mainSizer)
        
        # The frame is fitted with its contents.        
        mainSizer.Fit(self)
         
        mainPanel.Layout()
        
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
         
class PeriodicTableViewer(wx.Frame):
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
                
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Periodic table viewer", style=wx.DEFAULT_FRAME_STYLE&~(wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER))

        self._parent = parent
                
        mainPanel = wx.Panel(self,wx.ID_ANY)
                
        mainSizer = wx.GridBagSizer(0,0)
        mainSizer.SetEmptyCellSize((20,20))

        self.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)) 
        
        for i in _COLS:
            wid = wx.TextCtrl(mainPanel,wx.ID_ANY, value=str(i), size=(40,40), style = wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.TE_READONLY|wx.NO_BORDER)
            wid.SetBackgroundColour((230,230,220))
            mainSizer.Add(wid, (0,i), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        for i,v in enumerate(_ROWS):
            wid = wx.TextCtrl(mainPanel,wx.ID_ANY, value=str(v), size=(40,40), style = wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.TE_READONLY|wx.NO_BORDER)
            wid.SetBackgroundColour((230,230,220))
            mainSizer.Add(wid, (i+1,0), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        wid = wx.TextCtrl(mainPanel,wx.ID_ANY, value="*", size=(40,40), style = wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.TE_READONLY|wx.NO_BORDER)
        mainSizer.Add(wid, (6,3), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        wid = wx.TextCtrl(mainPanel,wx.ID_ANY, value="**", size=(40,40), style = wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.TE_READONLY|wx.NO_BORDER)
        mainSizer.Add(wid, (7,3), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        wid = wx.TextCtrl(mainPanel,wx.ID_ANY, value="*", size=(40,40), style = wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.TE_READONLY|wx.NO_BORDER)
        mainSizer.Add(wid, (9,3), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        wid = wx.TextCtrl(mainPanel,wx.ID_ANY, value="**", size=(40,40), style = wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.TE_READONLY|wx.NO_BORDER)
        mainSizer.Add(wid, (10,3), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        # The panel that will contain the short info about a selected element.
        self.shortInfo = ElementShortInfoPanel(mainPanel)
        mainSizer.Add(self.shortInfo, (1,5), (3,7), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)

        symbs = []
        for el in ELEMENTS.elements:
            info = ELEMENTS.get_element(el)
            if info['symbol'] in symbs:
                continue
            symbs.append(info['symbol'])
            try:
                r,c = _LAYOUT[info['symbol']]
                wid = wx.TextCtrl(mainPanel,wx.ID_ANY,value=info["symbol"],size=(40,40),style=wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.TE_READONLY|wx.NO_BORDER)
                wid.SetToolTipString(info['name'])
                bgColor = _FAMILY[info['family']]
                wid.SetBackgroundColour(bgColor)
                fgColor = _STATE[info['state']]
                wid.SetForegroundColour(fgColor)                                            
                wid.Bind(wx.EVT_LEFT_DOWN, self.on_select_element)
                wid.Bind(wx.EVT_ENTER_WINDOW, self.on_display_element_short_info)
                mainSizer.Add(wid, (r+1,c), flag=wx.ALL|wx.ALIGN_CENTER|wx.FIXED_MINSIZE|wx.EXPAND, border=1)
            except KeyError:
                continue
        
        edit = wx.Button(mainPanel,wx.ID_ANY,label="Edit element(s)")        
        mainSizer.Add(edit,(12,0),(1,19),flag=wx.EXPAND,border=20)
                                    
        mainPanel.SetSizer(mainSizer)
        self.SetSize(mainPanel.GetBestSize())

        self.Bind(wx.EVT_BUTTON,self.on_open_database,edit)
                               
    def on_open_database(self,event):
        
        f = ElementsDatabaseEditor(self)
        f.Show()

    def on_select_element(self, event=None):
                
        # The button of the periodic table that was clicked on.
        button = event.GetEventObject()
        
        element = button.GetValue()
        
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

        element = event.GetEventObject().GetValue()
            
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
        elementFrame = ElementInfoFrame(self, element)
        elementFrame.Show()
                  
if __name__ == "__main__":
    app = wx.App(False)
    f = PeriodicTableViewer(None)
    f.Show()
    app.MainLoop()    
