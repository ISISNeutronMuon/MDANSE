# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/MainFrame.py
# @brief     Implements module/class/test MainFrame
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import sys
import webbrowser


import wx
import wx.aui as aui
import wx.html as wxhtml
 
from MDANSE import LOGGER, PLATFORM, REGISTRY
from MDANSE.__pkginfo__ import __author__, __commit__, __version__, __beta__
from MDANSE.Core.Platform import PLATFORM
from MDANSE.Framework.Jobs.Converter import Converter
from MDANSE.GUI.ControllerPanel import ControllerPanel
from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.DataTreePanel import DataTreePanel
from MDANSE.GUI.Icons import ICONS
from MDANSE.GUI.PluginsTreePanel import PluginsTreePanel
from MDANSE.GUI.WorkingPanel import WorkingPanel

def excepthook(error, message, tback):
    '''
    Called when an exception is raised and uncaught.
    
    Redirect the exception information to the MDANSE logger at the ERROR level.
        
    :param typ: the exception class.
    :type typ: exception
    
    @param value: the exception instance.
    @type value: exception
    
    @param tback: the traceback.
    @type tback: traceback instance  
    '''
    
    import traceback
    
    from MDANSE.Core.Error import Error

    tback = traceback.extract_tb(tback)

    trace = []                        

    if not issubclass(error, Error):
        for tb in tback:
            trace.append(' -- '.join([str(t) for t in tb]))
    
    trace.append("\n%s: %s" % (error.__name__,message))

    trace = '\n'.join(trace)
                
    LOGGER(trace,'error',['console','dialog'])
        
class MainFrame(wx.Frame):

    def __init__(self, parent, title="MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments"):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, title, size = (1200,800))
    
        self.build_dialog()
        
        # Add some handlers to the loggers
        consoleHandler = REGISTRY['handler']['console'](self._panels["controller"].pages["logger"])
        LOGGER.add_handler("console", consoleHandler, level="info")
        LOGGER.add_handler("dialog", REGISTRY['handler']['dialog'](), level="error")
        LOGGER.start()
        
        # Redirect all output to the console logger
        sys.stdout = consoleHandler
        sys.stderr = consoleHandler
                
        sys.excepthook = excepthook
                 
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
        paneInfo1=aui.AuiPaneInfo()
        paneInfo2=aui.AuiPaneInfo()
        # Order is first "Data", and then "Plugins". It is switched on Linux and macOS
        if PLATFORM.name == "windows":
            self._mgr.AddPane(self._panels["data"], paneInfo1.Caption("Data").Name("data").Left().CloseButton(True).DestroyOnClose(False).MinSize((250,-1)))
            self._mgr.AddPane(self._panels["plugins"], paneInfo2.Caption("Plugins").Name("plugins").Left().CloseButton(True).DestroyOnClose(False).MinSize((250,-1)))
        else:
            self._mgr.AddPane(self._panels["plugins"], paneInfo2.Caption("Plugins").Name("plugins").Left().CloseButton(True).DestroyOnClose(False).MinSize((250,-1)))
            self._mgr.AddPane(self._panels["data"], paneInfo1.Caption("Data").Name("data").Left().CloseButton(True).DestroyOnClose(False).MinSize((250,-1)))
        paneInfo3=aui.AuiPaneInfo()
        self._mgr.AddPane(self._panels["working"], paneInfo3.Caption("Working panel").Name("working").Center().CloseButton(False))
        paneInfo4=aui.AuiPaneInfo()
        self._mgr.AddPane(self._panels["controller"], paneInfo4.Name("controller").Name("controller").Floatable().Right().Bottom().CloseButton(True).DestroyOnClose(False).MinSize((-1,120)))

        self._mgr.Update()

    def build_menu(self):
        
        self._mainMenu = wx.MenuBar()

        fileMenu = wx.Menu()
        loadDataItem = fileMenu.Append(wx.ID_ANY, 'Load data')
        fileMenu.AppendSeparator()
        converterMenu = wx.Menu()
        self._converters = {}

        converters = [job for job in REGISTRY["job"].items() if issubclass(job[1],Converter)]
        converters = sorted(converters)
        for name,job in converters:
            item = converterMenu.Append(wx.ID_ANY,job.label)
            self._converters[job.label] = name
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
        helpMenu.AppendSeparator()
        simpleHelpItem = helpMenu.Append(wx.ID_ANY, 'Simple help')
        theoryHelpItem = helpMenu.Append(wx.ID_ANY, 'Theoretical background')
        user_guideHelpItem = helpMenu.Append(wx.ID_ANY, 'User guide')
        helpMenu.AppendSeparator()
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
        self.Bind(wx.EVT_MENU, self.on_simple_help, simpleHelpItem)
        self.Bind(wx.EVT_MENU, self.on_theory_help, theoryHelpItem)
        self.Bind(wx.EVT_MENU, self.on_user_guide, user_guideHelpItem)

    def build_toolbar(self):
        
        self._toolbar = self.CreateToolBar()
                
        loadDataButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["load",32,32], 'Load a trajectory')
        periodicTableButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["periodic_table",32,32], 'Launch the periodic table viewer')
        elementsDatabaseButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["atom",32,32], 'Launch the elements database editor')
        plotButton = self._toolbar.AddSimpleTool(wx.ID_ANY,ICONS["plot",32,32], 'Launch the NetCDF plotter')
        udButton = self._toolbar.AddSimpleTool(wx.ID_ANY,ICONS["user",32,32], 'Launch the user definitions editor')
        registryButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["registry",32,32], 'Inspect MDANSE classes framework')
        templateButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["template",32,32], 'Save a template for a new analysis')
        apiButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["api",32,32], 'Open MDANSE API')
        websiteButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["web",32,32], 'Open MDANSE website')
        aboutButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["about",32,32], 'About MDANSE')
        bugButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["bug",32,32], 'Bug report')
        quitButton = self._toolbar.AddSimpleTool(wx.ID_ANY, ICONS["quit",32,32], 'Quit MDANSE')
        
        self._toolbar.Realize()
        
        self.SetToolBar(self._toolbar)

        # The toolbar-related events handlers.
        self.Bind(wx.EVT_MENU, self.on_load_data, loadDataButton)
        self.Bind(wx.EVT_MENU, self.on_open_periodic_table, periodicTableButton)
        self.Bind(wx.EVT_MENU, self.on_open_elements_database, elementsDatabaseButton)
        self.Bind(wx.EVT_MENU, self.on_start_plotter, plotButton)
        self.Bind(wx.EVT_MENU, self.on_open_user_definitions, udButton)
        self.Bind(wx.EVT_MENU, self.on_open_classes_registry, registryButton)
        self.Bind(wx.EVT_MENU, self.on_save_job_template, templateButton)
        self.Bind(wx.EVT_MENU, self.on_about, aboutButton)
        self.Bind(wx.EVT_MENU, self.on_quit, quitButton)
        self.Bind(wx.EVT_MENU, self.on_open_api, apiButton)
        self.Bind(wx.EVT_MENU, self.on_open_mdanse_url, websiteButton)
        self.Bind(wx.EVT_MENU, self.on_bug_report, bugButton)
                                                                    
    def load_data(self,typ,filename):
        if typ == "automatic":
            # if type is set on automatic, find data type
            if filename[-4:] == ".mvi":
                # File is mvi
                typ = "molecular_viewer"
                data = REGISTRY["input_data"]["molecular_viewer"](filename)
            else:
                # File is either netcdf or mmtk
                try:
                    data = REGISTRY["input_data"]["mmtk_trajectory"](filename)
                except KeyError:
                    data = REGISTRY["input_data"]["netcdf_data"](filename)
        else:
            data = REGISTRY["input_data"][typ](filename)

        DATA_CONTROLLER[data.filename] = data

    def on_about(self, event=None):
        if __beta__:
            beta_string = " (%s)" % __beta__
        else:
            beta_string = ""
        about_str = \
"""MDANSE version %s (commit %s).

An interactive program for analyzing Molecular Dynamics simulations.

Authors:
""" % (__version__ + beta_string,__commit__)

        for author in __author__.split(","):
            about_str += "\t- %s\n" % author.strip()
        
        d = wx.MessageDialog(self, about_str, 'About', style=wx.OK|wx.ICON_INFORMATION)
        d.ShowModal()
        d.Destroy()

    def on_bug_report(self, event=None):

        webbrowser.open("mailto:mdanse@ill.fr?subject=MDANSE query")        

    def on_simple_help(self,event):

        path = os.path.join(PLATFORM.doc_path(),'simple_help.html')
                
        with open(path,'r') as f:
            info = f.read()
            frame = wx.Frame(self, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)
            frame.SetMinSize((800,600))
            panel = wx.Panel(frame,wx.ID_ANY)
            sizer = wx.BoxSizer(wx.VERTICAL)
            html = wxhtml.HtmlWindow(panel, -1, size=(300, 150), style=wx.VSCROLL|wx.HSCROLL|wx.TE_READONLY|wx.BORDER_SIMPLE)
            html.SetPage(info)
            sizer.Add(html,1,wx.ALL|wx.EXPAND,5)
            panel.SetSizer(sizer)
            frame.Show()

    @staticmethod
    def on_theory_help(event):
        webbrowser.open("file://%s" % os.path.join(PLATFORM.doc_path(),'theory_help.pdf'))

    @staticmethod
    def on_user_guide(event):
        webbrowser.open("https://doi.org/10.5286/raltr.2022003")
                
    def on_open_classes_registry(self,event):
        
        from MDANSE.GUI.RegistryViewer import RegistryViewer
        
        f = RegistryViewer(self)
        
        f.ShowModal()
        
        f.Destroy()
        
    def on_save_job_template(self,event):
        
        from MDANSE.GUI.JobTemplateEditor import JobTemplateEditor
        
        f = JobTemplateEditor(self)
        
        f.ShowModal()
        
        f.Destroy()

    def on_open_api(self, event):
        
        mainHTML = os.path.join(PLATFORM.api_path(),'MDANSE.html')
        
        if os.path.exists(mainHTML):
            webbrowser.open("file://%s" % mainHTML)
        else:
            LOGGER("Can not open MDANSE API. Maybe the documentation was not properly installed.", "error",['dialog'])
            
    def on_load_data(self, event=None):

        wildcards = collections.OrderedDict([kls._type, "%s (*.%s)|*.%s" % (kls._type,kls.extension,kls.extension)] for kls in REGISTRY["input_data"].values() if kls.extension is not None)

        dialog = wx.FileDialog ( None, message='Open data ...', wildcard="automatic (*.mvi,*.nc,*.h5)|*.mvi;*.nc;*.h5|" + "|".join(wildcards.values()), style=wx.OPEN)
        
        if dialog.ShowModal() == wx.ID_CANCEL:
            return ""
                
        idx = dialog.GetFilterIndex()
        # Check if automatic has been chosen
        if idx <= 0:
            dataType = "automatic"
        else:
            dataType = wildcards.keys()[idx-1]
                        
        filename = dialog.GetPath()
        
        if not filename:
            return
        
        self.load_data(dataType,filename)
                
        LOGGER("Data %r successfully loaded." % filename, "info", ["console"])
                                                            
    def on_open_user_definitions(self,event):
        
        from MDANSE.GUI.UserDefinitionViewer import UserDefinitionViewer
        
        f = UserDefinitionViewer(self)
        f.ShowModal()
        f.Destroy()

    def on_open_converter(self,event):

        from MDANSE.GUI.Plugins.JobPlugin import JobFrame

        item = self.GetMenuBar().FindItemById(event.GetId())
        converter = item.GetText()
                        
        f = JobFrame(self,self._converters[converter],None)
        f.Show()

    def on_open_periodic_table(self, event):

        from MDANSE.GUI.PeriodicTableViewer import PeriodicTableViewer
                
        f = PeriodicTableViewer(self)
        
        f.Show()

    def on_open_elements_database(self, event):

        from MDANSE.GUI.ElementsDatabaseEditor import ElementsDatabaseEditor
                
        f = ElementsDatabaseEditor(self)
        
        f.Show()

    def on_open_mdanse_url(self, event):

        webbrowser.open('http://mdanse.org')

    def on_quit(self, event=None):
        
        d = wx.MessageDialog(None, 'Do you really want to quit ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()
                                                                         
    def on_start_plotter(self, event = None):

        from MDANSE.GUI.Plugins.PlotterPlugin import PlotterFrame
        
        f = PlotterFrame(self)
        
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

        self._prevSize = self.GetSize()

        if self.GetToolBar():
            sizeH = self._prevSize[1] - self._toolbar.GetSize()[1]
            self._toolbar.Hide()
            self.SetToolBar(None)
        else:
            sizeH = self._prevSize[1] + self._toolbar.GetSize()[1]
            self.SetToolBar(self._toolbar)
            self._toolbar.Show()
            
        self.SetSize((-1,sizeH))
            
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
    
    from MDANSE.GUI.Apps import MainApplication
    
    app = MainApplication(None)
    app.MainLoop()
