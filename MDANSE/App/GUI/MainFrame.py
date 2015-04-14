import collections
import webbrowser

import wx
import wx.aui as aui

from MDANSE.__pkginfo__ import __version__, __revision__
from MDANSE import LOGGER, REGISTRY

from MDANSE.App.GUI import DATA_CONTROLLER
from MDANSE.App.GUI.ControllerPanel import ControllerPanel
from MDANSE.App.GUI.DataTreePanel import DataTreePanel
from MDANSE.App.GUI.Icons import ICONS
from MDANSE.App.GUI.PluginsTreePanel import PluginsTreePanel
from MDANSE.App.GUI.WorkingPanel import WorkingPanel

class MainFrame(wx.Frame):

    def __init__(self, parent, title="MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments"):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, size = (1200,800))
  
        self.build_dialog()
        
        # Add some handlers to the loggers
        LOGGER.add_handler("console", REGISTRY['handler']['console'](self._panels["controller"].pages["logger"]), level="info")
        LOGGER.add_handler("dialog", REGISTRY['handler']['dialog'], level="error")
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
        emptyDataItem = fileMenu.Append(wx.ID_ANY, 'Open empty data')
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
        self.Bind(wx.EVT_MENU, self.on_load_empty_data, emptyDataItem)
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
        emptyDataButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["empty_data",32,32], 'Open an empty data (converters ...)')
        databaseButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["periodic_table",32,32], 'Edit the MDANSE elements database')
        plotButton = self._toolbar.AddSimpleTool(wx.ID_ANY,ICONS["plot",32,32], 'Open MDANSE plotter')
        userButton = self._toolbar.AddSimpleTool(wx.ID_ANY,ICONS["user",32,32], 'Edit the user definitions')
        preferencesButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["preferences",32,32], 'Edit the preferences')
        logfileButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["logfile",32,32], 'Display nMOLDYN log file')
        helpButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["help",32,32], 'Help')
        websiteButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["web",32,32], 'Open MDANSE website')
        aboutButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["about",32,32], 'About MDANSE')
        bugButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["bug",32,32], 'Bug report')
        quitButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["quit",32,32], 'Quit MDANSE')
        
        self._toolbar.Realize()
        
        self.SetToolBar(self._toolbar)

        # The toolbar-related events handlers.
        self.Bind(wx.EVT_MENU, self.on_load_data, loadDataButton)
        self.Bind(wx.EVT_MENU, self.on_load_empty_data, emptyDataButton)
        self.Bind(wx.EVT_MENU, self.on_open_nmoldyn_elements_database, databaseButton)
        self.Bind(wx.EVT_MENU, self.on_start_plotter, plotButton)
        self.Bind(wx.EVT_MENU, self.on_start_UDviewer, userButton)
        self.Bind(wx.EVT_MENU, self.on_set_preferences, preferencesButton)
        self.Bind(wx.EVT_MENU, self.on_display_logfile, logfileButton)
        self.Bind(wx.EVT_MENU, self.on_about, aboutButton)
        self.Bind(wx.EVT_MENU, self.on_quit, quitButton)
        self.Bind(wx.EVT_MENU, self.on_help, helpButton)
        self.Bind(wx.EVT_MENU, self.on_open_nmoldyn_url, websiteButton)
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

for any other request, do not hesitate to send an email to:

\tpellegrini@ill.fr
\tjohnson@ill.fr
\tgonzalezm@ill.fr

or directly to the MDANSE mailing list:

\tmdanse@ill.fr
"""
        
        d = wx.MessageDialog(self, report_str, 'Bug report', style=wx.OK|wx.ICON_INFORMATION)
        d.ShowModal()
        d.Destroy()
        
    def on_display_logfile(self,event):
        
        from nMOLDYN.GUI.Widgets.LogfileFrame import LogfileFrame
        
        f = LogfileFrame(self)
        
        f.Show()

    def on_help(self, event):

        webbrowser.open('http://www.ill.eu/fileadmin/users_files/img/instruments_and_support/support_facilities/computing_for_science/Computing_for_Science/CS_Software/nMoldyn/documentation/index.html')
            
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
                                                            
    def on_load_empty_data(self,event):
        
        self.load_data('empty_data', None)

    def on_open_nmoldyn_elements_database(self, event):

        from nMOLDYN.Framework.Plugins.PeriodicTablePlugin import PeriodicTableFrame
                
        f = PeriodicTableFrame(None)
        
        f.Show()

    def on_open_nmoldyn_url(self, event):

        webbrowser.open('http://www.ill.eu/fr/instruments-support/computing-for-science/cs-software/all-software/nmoldyn/')

    def on_quit(self, event=None):
        d = wx.MessageDialog(None, 'Do you really want to quit ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()

    def on_set_preferences(self, event):

        from nMOLDYN.GUI.Widgets.PreferencesSettingsDialog import PreferencesSettingsDialog
        
        d = PreferencesSettingsDialog(self)
        
        d.ShowModal()
        
        d.Destroy()
                                                                         
    def on_start_plotter(self, event = None):

        from nMOLDYN.Framework.Plugins.PlotterPlugin import PlotterFrame
        
        f = PlotterFrame(None)
        
        f.Show()                                               
        
    def on_start_UDviewer(self, event = None):

        from nMOLDYN.Framework.Plugins.UserDefinitionViewerPlugin import UserDefinitionViewerFrame
        
        f = UserDefinitionViewerFrame(None)
        
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
