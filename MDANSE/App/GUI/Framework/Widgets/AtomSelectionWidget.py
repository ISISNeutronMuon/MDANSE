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
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

import collections
import os

import wx

from MDANSE import LOGGER, REGISTRY
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.AtomSelectionParser import AtomSelectionParser, AtomSelectionParserError
from MDANSE.Framework.Configurable import ConfigurationError
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

from MDANSE.App.GUI.Framework.Widgets.UserDefinitionWidget import UserDefinitionsDialog, UserDefinitionWidget
from MDANSE.App.GUI.Framework.Plugins.DataPlugin import get_data_plugin 

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
            if self._list:
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

class AtomSelectionDialog(UserDefinitionsDialog):
    
    def __init__(self, parent, trajectory, *args, **kwargs):

        self._query = Query()

        self._selectors = {}
                                        
        self._selection = []

        self._trajectory = trajectory
        
        self._query.set_parser(AtomSelectionParser(self._trajectory.universe))

        self._atoms = sorted_atoms(self._trajectory.universe)  
        
        target = os.path.basename(self._trajectory.filename)
        
        UserDefinitionsDialog.__init__(self, parent, target, 'atom_selection', wx.ID_ANY, title="Atom selection dialog",style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)

        pub.subscribe(self.on_select_atoms_from_viewer, ('select_atoms_from_viewer'))       
                 
    def build_dialog(self):
                                                
        self._mainPanel = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        self._mainPanel.SetScrollbars(20,20,50,50)

        sizer = wx.BoxSizer(wx.VERTICAL)
        
        settingsPanel = wx.Panel(self._mainPanel,wx.ID_ANY)
                
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
                                         
        selectionSizer = wx.BoxSizer(wx.VERTICAL)
        selectionSizer.Add(self._queryPanel,1,wx.ALL|wx.EXPAND,5)
         
        settingsPanel.SetSizer(selectionSizer)

        # The widgets related to the selection being performed        
        selectionExpressionStaticBox = wx.StaticBox(self._mainPanel, wx.ID_ANY, label = "Selection")                
        selectionExpressionStaticBoxSizer = wx.StaticBoxSizer(selectionExpressionStaticBox, wx.HORIZONTAL)

        self.selectionTextCtrl = wx.TextCtrl(self._mainPanel, wx.ID_ANY, style = wx.TE_READONLY)
        clearButton = wx.Button(self._mainPanel, wx.ID_ANY, label="Clear")
        
        self._selectionExpressionSizer = wx.GridBagSizer(5,5)        
        self._selectionExpressionSizer.AddGrowableCol(0)
        self._selectionExpressionSizer.Add(self.selectionTextCtrl, pos=(0,0), span=(1,2),flag=wx.ALL|wx.EXPAND)
        self._selectionExpressionSizer.Add(clearButton, pos=(0,2), flag=wx.ALL)
        selectionExpressionStaticBoxSizer.Add(self._selectionExpressionSizer,1,wx.ALL|wx.EXPAND,5)
                    
        self._selectionSummary = wx.TextCtrl(self._mainPanel,wx.ID_ANY,style=wx.TE_LINEWRAP|wx.TE_MULTILINE|wx.TE_READONLY)  
                                                   
        sizer.Add(settingsPanel, 2, wx.ALL|wx.EXPAND, 5)
        sizer.Add(selectionExpressionStaticBoxSizer, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self._selectionSummary, 1, wx.ALL|wx.EXPAND, 5)

        self._mainPanel.SetSizer(sizer)
                                                                              
        self._mainSizer.Add(self._mainPanel, 1, wx.EXPAND|wx.ALL, 5)
                                                                              
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_display_keyword_values, self.filterTree)
        self.Bind(wx.EVT_LISTBOX, self.on_insert_keyword_values, self.values)
  
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, leftBraceLinker)
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, rightBraceLinker)
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, orLinker)
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, andLinker)
        self.Bind(wx.EVT_BUTTON, self.on_add_operator, notLinker)
            
        self.Bind(wx.EVT_BUTTON, self.on_clear, clearButton)
                        
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
        
        self._selectionSummary.Clear()

        pub.sendMessage('clear_selection',message=self)                                

    def on_close(self, event=None):
        
        self.Destroy()
                
    def on_display_keyword_values(self, event=None):
        
        if self._trajectory is None:
            return
        
        item = event.GetItem()

        selectionFilter = self.filterTree.GetItemText(item)
        
        if not REGISTRY["selector"].has_key(selectionFilter):
            return
                                
        if not self._selectors.has_key(selectionFilter):
            self._selectors[selectionFilter] = [str(v) for v in REGISTRY["selector"][selectionFilter](self._trajectory.universe).choices]
        
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

    def on_select_atoms_from_viewer(self, message):

        dataPlugin,selection = message
        
        if dataPlugin != get_data_plugin(self):
            return
        
        self._query.clear()
        
        self.insert_keyword_values("atom_picked", selection)
                
    def set_selection(self):

        _, selection = self._query.parse()
                
        pub.sendMessage("set_selection", message = (self,selection))
        
    def validate(self):

        if not self._ud:
            LOGGER("The current selection is empty", "error", ["dialog"])
            return None
        
        return self._ud

class AtomSelectionWidget(UserDefinitionWidget):
        
    type = "atom_selection"

    def on_new_user_definition(self,event):
        
        dlg = AtomSelectionDialog(self,self._trajectory)
        
        dlg.Show()
         
if __name__ == "__main__":
    
    from MMTK.Trajectory import Trajectory
    
    t = Trajectory(None,"../../../../../Data/Trajectories/MMTK/protein_in_periodic_universe.nc","r")
    
    app = wx.App(False)
    
    p = AtomSelectionDialog(None,t)
        
    p.SetSize((800,800))
            
    p.ShowModal()
    
    p.Destroy()
    
    app.MainLoop()
        