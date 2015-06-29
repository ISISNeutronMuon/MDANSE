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

:author: Bachir Aoun, Gael Goret and Eric C. Pellegrini
'''

import collections
import operator
import os
import webbrowser

import wx
import wx.aui as aui

from MDANSE.__pkginfo__ import __version__, __revision__
from MDANSE import LOGGER, PLATFORM, REGISTRY
from MDANSE.Framework.Jobs.Converters.Converter import Converter

from MDANSE.App.GUI import DATA_CONTROLLER
from MDANSE.App.GUI.ControllerPanel import ControllerPanel
from MDANSE.App.GUI.DataTreePanel import DataTreePanel
from MDANSE.App.GUI.Icons import ICONS
from MDANSE.App.GUI.WorkingPanel import WorkingPanel
from MDANSE.App.GUI.PluginsTreePanel import PluginsTreePanel

class MainFrame(wx.Frame):

    def __init__(self, parent, title="MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments"):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, size = (1200,800))
  
        self.build_dialog()
        
        # Add some handlers to the loggers
        LOGGER.add_handler("console", REGISTRY['handler']['console'](self._panels["controller"].pages["logger"]), level="info")
        LOGGER.add_handler("dialog", REGISTRY['handler']['dialog'](), level="error")
        LOGGER.start()
                                
    def build_dialog(self):
        
        self.build_menu()
        
        self.build_toolbar()

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(ICONS["mdanse",32,32])
        self.SetIcon(icon) 
        
        # The main aui manager.
        self._mgr = aui.AuiManager(self)

        self._panels = {}
        self._panels["data"] = DataTreePanel(self)
        self._panels["plugins"] = PluginsTreePanel(self)
        self._panels["working"] = WorkingPanel(self)
        self._panels["controller"] = ControllerPanel(self)
        
        # Add the panes corresponding to the tree control and the notebook.
        paneInfo=aui.AuiPaneInfo()
        self._mgr.AddPane(self._panels["data"], paneInfo.Caption("Data").Name("data").Left().CloseButton(True).DestroyOnClose(False).MinSize((250,-1)))
        self._mgr.AddPane(self._panels["plugins"], paneInfo.Caption("Plugins").Name("plugins").Left().CloseButton(True).DestroyOnClose(False).MinSize((250,-1)))
        self._mgr.AddPane(self._panels["working"], paneInfo.Name("working").Center().CloseButton(False))
        self._mgr.AddPane(self._panels["controller"], paneInfo.Name("controller").Name("controller").Floatable().Right().Bottom().CloseButton(True).DestroyOnClose(False).MinSize((-1,120)))

        self._mgr.Update()

    def build_menu(self):
        
        self._mainMenu = wx.MenuBar()

        fileMenu = wx.Menu()
        loadDataItem = fileMenu.Append(wx.ID_ANY, 'Load data')
        fileMenu.AppendSeparator()
        converterMenu = wx.Menu()
        self._converters = {}

        converters = [job for job in REGISTRY["job"].values() if issubclass(job,Converter)]
        converters = sorted(converters, key = operator.attrgetter('label'))
        for job in converters:
            item = converterMenu.Append(wx.ID_ANY,job.label)
            self._converters[job.label] = job.type
            self.Bind(wx.EVT_MENU, self.on_open_converter, item)

        fileMenu.AppendMenu(wx.ID_ANY,'Trajectory converters',converterMenu)
        fileMenu.AppendSeparator()
        quitItem = fileMenu.Append(wx.ID_ANY, 'Quit')

        self._mainMenu.Append(fileMenu, 'File')

        viewMenu = wx.Menu()
        showDataTreeItem = viewMenu.Append(wx.ID_ANY, "Toggle data tree")
        showPluginsTreeItem = viewMenu.Append(wx.ID_ANY, "Toggle plugins tree")
        showControllerItem = viewMenu.Append(wx.ID_ANY, "Toggle controller")
        viewMenu.AppendSeparator()
        showToolbarItem = viewMenu.Append(wx.ID_ANY, "Toggle toolbar")

        self._mainMenu.Append(viewMenu, 'View')

        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ANY, 'About')
        bugReportItem = helpMenu.Append(wx.ID_ANY, 'Bug report')
        self._mainMenu.Append(helpMenu, 'Help')

        self.SetMenuBar(self._mainMenu)

        self.Bind(wx.EVT_CLOSE, self.on_quit)
        
        self.Bind(wx.EVT_MENU, self.on_load_data, loadDataItem)
        self.Bind(wx.EVT_MENU, self.on_quit, quitItem)
        self.Bind(wx.EVT_MENU, self.on_about, aboutItem)
        self.Bind(wx.EVT_MENU, self.on_toggle_data_tree, showDataTreeItem)
        self.Bind(wx.EVT_MENU, self.on_toggle_plugins_tree, showPluginsTreeItem)
        self.Bind(wx.EVT_MENU, self.on_toggle_controller, showControllerItem)
        self.Bind(wx.EVT_MENU, self.on_toggle_toolbar, showToolbarItem)
        self.Bind(wx.EVT_MENU, self.on_bug_report, bugReportItem)

    def build_toolbar(self):
        
        self._toolbar = self.CreateToolBar()
                
        loadDataButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["load",32,32], 'Load a trajectory')
        databaseButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["periodic_table",32,32], 'Edit the MDANSE elements database')
        plotButton = self._toolbar.AddSimpleTool(wx.ID_ANY,ICONS["plot",32,32], 'Open MDANSE plotter')
        udButton = self._toolbar.AddSimpleTool(wx.ID_ANY,ICONS["user",32,32], 'Edit the user definitions')
        preferencesButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["preferences",32,32], 'Edit the preferences')
        registryButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["registry",32,32], 'Inspect MDANSE classes registry')
        apiButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["api",32,32], 'Open MDANSE API')
        websiteButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["web",32,32], 'Open MDANSE website')
        aboutButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["about",32,32], 'About MDANSE')
        bugButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["bug",32,32], 'Bug report')
        quitButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["quit",32,32], 'Quit MDANSE')
        
        self._toolbar.Realize()
        
        self.SetToolBar(self._toolbar)

        # The toolbar-related events handlers.
        self.Bind(wx.EVT_MENU, self.on_load_data, loadDataButton)
        self.Bind(wx.EVT_MENU, self.on_open_mdanse_elements_database, databaseButton)
        self.Bind(wx.EVT_MENU, self.on_start_plotter, plotButton)
        self.Bind(wx.EVT_MENU, self.on_set_preferences, preferencesButton)
        self.Bind(wx.EVT_MENU, self.on_open_user_definitions, udButton)
        self.Bind(wx.EVT_MENU, self.on_open_classes_registry, registryButton)
        self.Bind(wx.EVT_MENU, self.on_about, aboutButton)
        self.Bind(wx.EVT_MENU, self.on_quit, quitButton)
        self.Bind(wx.EVT_MENU, self.on_open_api, apiButton)
        self.Bind(wx.EVT_MENU, self.on_open_mdanse_url, websiteButton)
        self.Bind(wx.EVT_MENU, self.on_bug_report, bugButton)
                                                                    
    def load_data(self,typ,filename):
        
        data = REGISTRY["input_data"][typ](filename)

        DATA_CONTROLLER[data.filename] = data

    def on_about(self, event=None):
        
        if __revision__ is "undefined":
            rev=""
        else:
            rev=" (%s)" % __revision__
                        
        about_str = \
"""MDANSE version %s%s.

An interactive program for analyzing Molecular Dynamics simulations.

Authors:
\tEric C. Pellegrini
\tGael Goret
\tBachir Aoun
""" % (__version__,rev)
        
        d = wx.MessageDialog(self, about_str, 'About', style=wx.OK|wx.ICON_INFORMATION)
        d.ShowModal()
        d.Destroy()

    def on_bug_report(self, event=None):
        report_str = \
"""The version 1 of MDANSE is currently under testing.
In order to facilitate the integration of new features and bug fixes, please send pull request to: 

https://github.com/eurydyce/MDANSE/tree/master/MDANSE

for any other request, please send an email to:

\tpellegrini@ill.fr
\tgonzalezm@ill.fr
\tjohnson@ill.fr

or directly to the MDANSE mailing list:

\tmdanse@ill.fr
"""
        
        d = wx.MessageDialog(self, report_str, 'Bug report', style=wx.OK|wx.ICON_INFORMATION)
        d.ShowModal()
        d.Destroy()
        
    def on_open_classes_registry(self,event):
        
        from MDANSE.App.GUI.Framework.Plugins.RegistryViewerPlugin import RegistryViewerFrame
        
        f = RegistryViewerFrame(self)
        
        f.Show()

    def on_open_api(self, event):
        
        mainHTML = os.path.join(PLATFORM.api_path(),'MDANSE.html')

        if os.path.exists(mainHTML):
            webbrowser.open(mainHTML)
        else:
            LOGGER("Can not open MDANSE API. Maybe the documentation was not properly installed.", "error",['dialog'])
            
    def on_load_data(self, event=None):

        wildcards = collections.OrderedDict([kls.type, "%s (*.%s)|*.%s" % (kls.type,kls.extension,kls.extension)] for kls in REGISTRY["input_data"].values() if kls.extension is not None)
                
        dialog = wx.FileDialog ( None, message='Open data ...', wildcard="|".join(wildcards.values()), style=wx.OPEN)
        
        if dialog.ShowModal() == wx.ID_CANCEL:
            return ""
                
        idx = dialog.GetFilterIndex()
                                                
        dataType = wildcards.keys()[idx]
                        
        filename = dialog.GetPath()
        
        if not filename:
            return
        
        self.load_data(dataType,filename)
                
        LOGGER("Data %r successfully loaded" % filename, "info")
                                                            
    def on_open_user_definitions(self,event):
        
        from MDANSE.App.GUI.Framework.Plugins.UserDefinitionViewerPlugin import UserDefinitionViewerFrame
        
        f = UserDefinitionViewerFrame(self)
        f.Show()

    def on_open_converter(self,event):

        item = self.GetMenuBar().FindItemById(event.GetId())
        convLabel = item.GetText()
        
        from MDANSE.App.GUI.Framework.Plugins.JobPlugin import JobFrame
        
        f = JobFrame(self,self._converters[convLabel])
        f.Show()

    def on_open_mdanse_elements_database(self, event):

        from MDANSE.App.GUI.Framework.Plugins.PeriodicTablePlugin import PeriodicTableFrame
                
        f = PeriodicTableFrame(None)
        
        f.Show()

    def on_open_mdanse_url(self, event):

        webbrowser.open('https://github.com/eurydyce/MDANSE/tree/master/MDANSE')

    def on_quit(self, event=None):
        
        d = wx.MessageDialog(None, 'Do you really want to quit ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()

    def on_set_preferences(self, event):

        from MDANSE.App.GUI.PreferencesSettingsDialog import PreferencesSettingsDialog
        
        d = PreferencesSettingsDialog(self)
        
        d.ShowModal()
        
        d.Destroy()
                                                                         
    def on_start_plotter(self, event = None):

        from MDANSE.App.GUI.Framework.Plugins.Plotter.PlotterPlugin import PlotterFrame
        
        f = PlotterFrame(None)
        
        f.Show()                                               
                
    def on_toggle_controller(self, event=None):

        pane = self._mgr.GetPane("controller")        
        
        self.toggle_window(pane)


    def on_toggle_data_tree(self, event=None):

        pane = self._mgr.GetPane("data")        
        
        self.toggle_window(pane)
        
        
    def on_toggle_plugins_tree(self, event = None):
        
        pane = self._mgr.GetPane("plugins")
        
        self.toggle_window(pane)    

    
    def on_toggle_toolbar(self, event=None):

        if self.GetToolBar():
            self._toolbar.Hide()                                    
            self.SetToolBar(None)
        else:
            self.SetToolBar(self._toolbar)
            self._toolbar.Show()   
        
    @property
    def panels(self):
        return self._panels
        
    def toggle_window(self, window):
        
        if window.IsShown():
            window.Hide()
        else:
            window.Show()

        self._mgr.Update()
        

if __name__ == "__main__":
    
    app = wx.App(False)
    f = MainFrame(None)
    f.Show()
    app.MainLoop()
