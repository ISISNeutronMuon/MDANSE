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

@author: Eric C. Pellegrini
'''

import collections
import os

import wx
import wx.aui as wxaui

from MDANSE import LOGGER, REGISTRY, UD_STORE
from MDANSE.Core.Error import Error
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.AtomSelectionParser import AtomSelectionParser, AtomSelectionParserError
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

from MDANSE.App.GUI.Framework.Plugins.ComponentPlugin import ComponentPlugin
from MDANSE.App.GUI.ComboWidgets.UserDefinitionsPanel import UserDefinitionsPanel

class AtomSelectionPluginError(Error):
    pass

class Query(object):
        
    def __init__(self):
        
        self._list = []
        
        self._parser = None

    def get_expression(self):

        s = []
                 
        for v in self._list:
            
            if isinstance(v, list):
                keyword,arguments = v
                arguments = ",".join([str(val) for val in arguments])
                s.append("%s %s" % (keyword,arguments))
            else:
                s.append(v)
        
        return "".join(s)
        
    @property
    def list(self):
        return self._list
    
    @property
    def parser(self):
        return self._parser

    def add_operator(self, operator):

        if operator == "(":
            if self._list:
                if self._list[-1] == ")" or isinstance(self._list[-1], list):
                    return
            self._list.append("(")
            
        elif operator == ")":
            if self._list:
                if self._list[-1] == ")" or isinstance(self._list[-1], list):
                    if self._list.count(")") < self._list.count("("):
                        self._list.append(")")
        
        elif operator == "not":
            if self._list[-1] == ")":
                return
            self._list.append(" not ")
            
        elif operator in ["and","or"]:       
            if self._list:
                if self._list[-1] == ")" or isinstance(self._list[-1], list):
                    self._list.append(" %s " % operator)
    
    def add_query(self, query):

        if not self._list:
            if query is not None:
                self._list.append(query)            
        else:
            
            keyword, values = query

            if isinstance(self._list[-1], list):

                if self._list[-1][0] == keyword:
                    if values:
                        self._list[-1] = query
                    else:
                        del self._list[-1]
                else:
                    self._list.extend([' or ', query])
                        
            elif isinstance(self._list[-1], basestring):
                if self._list[-1] in [' and ',' or ','(',' not ']:
                    self._list.append(query)                    

    def clear(self):
        self._list = []
        
    def is_empty(self):
        
        return len(self._list) == 0
            
    def parse(self):
        
        if self._parser is None:
            return []
                            
        try:
            expression = self.get_expression()
            selection = self._parser.parse(expression)
        except AtomSelectionParserError:
            return ("",[])
        else:
            return (expression,selection)
            
    def pop(self):
        return self._list.pop()
    
    def set_parser(self, parser):
        
        self._parser = parser

class AtomSelectionPlugin(ComponentPlugin):

    type = "atom_selection"
    
    label = "Atom selection"
    
    ancestor = "molecular_viewer"
    
    def __init__(self, parent, *args, **kwargs):

        self._query = Query()

        self._selectors = {}
                                        
        self._expression = None

        self._selection = None

        self._selectionParser = None
        
        ComponentPlugin.__init__(self, parent, size = (500,450), *args, **kwargs)
                 
    def build_panel(self):
                                                
        self._mainPanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())

        self._notebook = wxaui.AuiNotebook(self._mainPanel, wx.ID_ANY, style=wxaui.AUI_NB_DEFAULT_STYLE&~wxaui.AUI_NB_CLOSE_ON_ACTIVE_TAB&~wxaui.AUI_NB_TAB_MOVE)
        
        settingsPanel = wx.Panel(self._mainPanel,wx.ID_ANY)
                
        self.keywordsRadioButton = wx.RadioButton(settingsPanel, wx.ID_ANY, label = "Keywords")
        self.keywordsRadioButton.SetValue(True)
        self.pythonScriptRadioButton = wx.RadioButton(settingsPanel, wx.ID_ANY, label = "Python script")
        self.mouseClickRadioButton = wx.RadioButton(settingsPanel, wx.ID_ANY, label = "Mouse click")
        self.boxWidgetRadioButton = wx.RadioButton(settingsPanel, wx.ID_ANY, label = "Box widget")

        # Build the widgets used to build a selection from selection strings and operators
        self._queryPanel = wx.Panel(settingsPanel)
                              
        self.filterTree = wx.TreeCtrl(self._queryPanel, 1, wx.DefaultPosition, style=wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS)
          
        root = self.filterTree.AddRoot("filters")
        filters = self.filterTree.AppendItem(root, "Filter by")
        selectors = REGISTRY["selector"].values()
        self.__filters = collections.OrderedDict()
        for selector in selectors:            
            if selector.section is not None:
                if self.__filters.has_key(selector.section):
                    self.__filters[selector.section].append(selector.type)
                else:
                    self.__filters[selector.section] = [selector.type]
         
        for section, subsections in sorted(self.__filters.items()):
            section_node = self.filterTree.AppendItem(filters, section)
            for subsection in sorted(subsections):
                self.filterTree.AppendItem(section_node,subsection)
         
        self.values = wx.ListBox(self._queryPanel, wx.ID_ANY, style = wx.LB_MULTIPLE|wx.LB_NEEDED_SB)
                                 
        leftBraceLinker = wx.Button(self._queryPanel, wx.ID_ANY, label = "(")        
        rightBraceLinker = wx.Button(self._queryPanel, wx.ID_ANY, label = ")")
        andLinker = wx.Button(self._queryPanel, wx.ID_ANY, label = "and")
        orLinker = wx.Button(self._queryPanel, wx.ID_ANY, label = "or")
        notLinker = wx.Button(self._queryPanel, wx.ID_ANY, label = "not")
         
        self._pythonScript = wx.Button(settingsPanel,wx.ID_ANY,label="Browse")
        self._pythonScript.Disable()

        self._selectionSummary = wx.TextCtrl(self._mainPanel,wx.ID_ANY,style=wx.TE_LINEWRAP|wx.TE_MULTILINE|wx.TE_READONLY)  
        
        self._notebook.AddPage(settingsPanel, "settings")
        self._notebook.AddPage(self._selectionSummary, "selection")

        selectionExpressionStaticBox = wx.StaticBox(self._mainPanel, wx.ID_ANY, label = "Selection")
                
        # The widgets related to the selection being performed        
        self.selectionTextCtrl = wx.TextCtrl(self._mainPanel, wx.ID_ANY, style = wx.TE_READONLY)
        clearButton  = wx.Button(self._mainPanel, wx.ID_ANY, label="Clear")
        undoButton  = wx.Button(self._mainPanel, wx.ID_ANY, label="Undo")

        # The panel related to user definition control
        self._udPanel = UserDefinitionsPanel(self._mainPanel)
                        
        selectionStringSizer = wx.BoxSizer(wx.VERTICAL)
        keywordsValuesSizer = wx.BoxSizer(wx.HORIZONTAL)
        keywordsValuesSizer.Add(self.filterTree, 1, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.EXPAND, 2)
        keywordsValuesSizer.Add(self.values, 3, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT|wx.EXPAND, 2)
        linkersSizer = wx.BoxSizer(wx.HORIZONTAL)
        linkersSizer.Add(leftBraceLinker, 1, flag=wx.ALL|wx.EXPAND)
        linkersSizer.Add(rightBraceLinker, 1, flag=wx.ALL|wx.EXPAND)
        linkersSizer.Add(andLinker, 1, flag=wx.ALL|wx.EXPAND)
        linkersSizer.Add(orLinker, 1, flag=wx.ALL|wx.EXPAND)
        linkersSizer.Add(notLinker, 1, flag=wx.ALL|wx.EXPAND)
        selectionStringSizer.Add(keywordsValuesSizer,1,wx.ALL|wx.EXPAND,5)
        selectionStringSizer.Add(linkersSizer,0,wx.ALL|wx.EXPAND,5)
        self._queryPanel.SetSizer(selectionStringSizer)
         
        selectionSizer = wx.GridBagSizer(5,5)
        selectionSizer.AddGrowableCol(1)
        selectionSizer.AddGrowableRow(1)
        selectionSizer.Add(self.keywordsRadioButton,pos=(0,0),span=(1,2))
        selectionSizer.Add((20,-1),pos=(1,0),flag=wx.EXPAND)
        selectionSizer.Add(self._queryPanel,pos=(1,1),flag=wx.EXPAND)
        selectionSizer.Add(self.pythonScriptRadioButton,pos=(2,0),span=(1,2))
        selectionSizer.Add((20,-1),pos=(3,0),flag=wx.EXPAND)
        selectionSizer.Add(self._pythonScript,pos=(3,1))
        selectionSizer.Add(self.mouseClickRadioButton,pos=(4,0),span=(1,2))
        selectionSizer.Add(self.boxWidgetRadioButton,pos=(5,0),span=(1,2))
         
        settingsPanel.SetSizer(selectionSizer)
        
        selectionExpressionStaticBoxSizer = wx.StaticBoxSizer(selectionExpressionStaticBox, wx.HORIZONTAL)
        self._selectionExpressionSizer = wx.GridBagSizer(5,5)        
        self._selectionExpressionSizer.AddGrowableCol(0)
        self._selectionExpressionSizer.Add(self.selectionTextCtrl, pos=(0,0), span=(1,2),flag=wx.ALL|wx.EXPAND)
        self._selectionExpressionSizer.Add(clearButton, pos=(0,2), flag=wx.ALL)
        self._selectionExpressionSizer.Add(undoButton, pos=(0,3), flag=wx.ALL)
        selectionExpressionStaticBoxSizer.Add(self._selectionExpressionSizer,1,wx.ALL|wx.EXPAND,5)
                                                   
        # Add to main sizer
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self._notebook, 1, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(selectionExpressionStaticBoxSizer, 0, wx.ALL|wx.EXPAND, 5)
        mainSizer.Add(self._udPanel, 0, wx.ALL|wx.EXPAND, 5)
                
        self._mainPanel.SetSizer(mainSizer)        
        mainSizer.Fit(self._mainPanel)
        self._mainPanel.Layout()
              
        self._mgr.AddPane(self._mainPanel, wxaui.AuiPaneInfo().DestroyOnClose().Center().Dock().CaptionVisible(False).CloseButton(False).BestSize(self.GetSize()))

        self._mgr.Update()
                                                                
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_display_keyword_values, self.filterTree)
        self.Bind(wx.EVT_LISTBOX, self.on_insert_keyword_values, self.values)
  
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, leftBraceLinker)
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, rightBraceLinker)
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, orLinker)
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, andLinker)
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, notLinker)
          
        self.Bind(wx.EVT_RADIOBUTTON, self.on_source_selection, self.keywordsRadioButton)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_source_selection, self.pythonScriptRadioButton)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_source_selection, self.mouseClickRadioButton)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_source_selection, self.boxWidgetRadioButton)
  
        self.Bind(wx.EVT_BUTTON, self.on_browse_python_script, self._pythonScript)
        self.Bind(wx.EVT_BUTTON, self.on_clear, clearButton)
        self.Bind(wx.EVT_BUTTON, self.on_undo, undoButton)
                
    def close(self):
        
        self.parent.selection_box.hide()
        self.parent.clear_selection()
        
    def display_selection_summary(self):
        
        self._selectionSummary.Clear()
        
        nSelectedAtoms = len(self._selection)
        
        self._selectionSummary.AppendText("Number of selected atoms: %d\n\n" % nSelectedAtoms)
        
        if nSelectedAtoms == 0:
            return
        
        self._selectionSummary.AppendText("List of selected atoms:\n")
        for idx in self._selection:
            self._selectionSummary.AppendText("\t%s (MMTK index: %d)\n" % (self._atoms[idx].fullName(),self._atoms[idx].index))

    def insert_keyword_values(self, keyword, values):

        self._query.add_query([keyword,values])
                
        self.set_selection()

        self.selectionTextCtrl.SetValue(self._query.get_expression())
        
        self.display_selection_summary()

    def on_add_operator(self, event=None):

        operator = event.GetEventObject().GetLabel()

        self._query.add_operator(operator)        
                
        self.selectionTextCtrl.SetValue(self._query.get_expression())
        
        self.values.DeselectAll()

    def on_browse_python_script(self, event):
        
        dlg = wx.FileDialog(self, "Browse python selection script", defaultDir=os.getcwd(), wildcard="Python files (*.py)|*.py",style=wx.FD_OPEN|wx.FD_MULTIPLE)

        if dlg.ShowModal() == wx.ID_OK:        
            self.insert_keyword_values("pythonscript", dlg.GetPaths())
                                                                                                                                                           
    def on_clear(self, event=None):
        
        self._query.clear()

        self.selectionTextCtrl.Clear()
                
        self.values.DeselectAll()
                                
        self._parent.clear_selection()     

    def on_close(self, event=None):
        
        self.close()
        self.parent.mgr.ClosePane(self.parent.mgr.GetPane(self))

    def on_display_keyword_values(self, event=None):
        
        if self._parent.trajectory is None:
            return
        
        item = event.GetItem()

        selectionFilter = self.filterTree.GetItemText(item)
        
        if not REGISTRY["selector"].has_key(selectionFilter):
            return
                                
        if not self._selectors.has_key(selectionFilter):
            self._selectors[selectionFilter] = [str(v) for v in REGISTRY["selector"][selectionFilter](self._parent.trajectory.universe).choices]
        
        self.values.Set(self._selectors[selectionFilter])

    def on_insert_keyword_values(self, event):
                                
        item = self.filterTree.GetSelection()
                
        keyword = str(self.filterTree.GetItemText(item))
                                
        values = [str(self.values.GetString(v)) for v in self.values.GetSelections()]

        self.insert_keyword_values(keyword, values)

    def on_mode_selection(self, event=None): 
        
        self.selectedMode = str(event.GetEventObject().GetLabelText()).lower()
        
        self.keywords.DeselectAll()
        self.values.DeselectAll()

    def on_save(self, event=None):
                
        if not self._selection:
            LOGGER("The current selection is empty", "error", ["dialog"])
            return
                       
        name = self._udPanel.get_selection_name()
        
        if not name:
            LOGGER("You must enter a value for the user definition", "error", ["dialog"])
            return
        
        path = os.path.basename(self.parent.trajectory.filename)
                    
        ud = REGISTRY['user_definition']['atom_selection'](path,expression=self._expression,indexes=self._selection)
            
        UD_STORE[name] = ud
        
        UD_STORE.save()
        
        pub.sendMessage("new_selection", message = (path, name))

    def on_select_atoms(self, message):
                
        self.insert_keyword_values("atompicked", message)

    def on_show_hide_selection_box(self, event=None):
        
        self._parent.show_hide_selection_box()

    def on_source_selection(self, event=None):
            
        selectedSource = str(event.GetEventObject().GetLabelText())
        
        if selectedSource == "Keywords":
            self._queryPanel.Enable()
            self._pythonScript.Disable()
            self._parent.selection_box.hide()
            self._parent.disable_picking()

        elif selectedSource == "Python script":
            self._queryPanel.Disable()
            self._pythonScript.Enable()
            self._parent.selection_box.hide()
            self._parent.disable_picking()
            
        elif selectedSource == "Mouse click":
            self._queryPanel.Disable()
            self._pythonScript.Disable()
            self._parent.selection_box.hide()
            self._parent.enable_picking()
            
        elif selectedSource == "Box widget":
            self._queryPanel.Disable()
            self._pythonScript.Disable()
            self._parent.selection_box.show()
            self._parent.disable_picking()

    def on_undo(self, event=None):

        if self._query.is_empty():
            return
                
        self._query.pop()
        
        self.set_selection()

        self.selectionTextCtrl.SetValue(self._query.get_expression())

    def plug(self):
        
        self.parent.mgr.GetPane(self).Float().Dockable(False).CloseButton(True).BestSize((600,600))

        self.parent.mgr.Update()
        
        self._query.set_parser(AtomSelectionParser(self.dataproxy.data.universe))
        
        self._atoms = sorted_atoms(self.dataproxy.data.universe)  

        pub.subscribe(self.on_select_atoms, ('select atoms'))       

    def set_selection(self):

        self._expression, self._selection = self._query.parse()
        
        self._parent.show_selected_atoms(self._selection)