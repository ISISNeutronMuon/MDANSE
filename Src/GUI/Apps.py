import wx

from MDANSE.GUI.Plugins.PlotterPlugin import PlotterFrame
from MDANSE.GUI.ElementsDatabaseEditor import ElementsDatabaseEditor
from MDANSE.GUI.MainFrame import MainFrame
from MDANSE.GUI.PeriodicTableViewer import PeriodicTableViewer
from MDANSE.GUI.UserDefinitionViewer import UserDefinitionViewer

class ElementsDatabaseEditorApp(wx.App):
    
    def OnInit(self):
        
        f = ElementsDatabaseEditor(None)
        f.Show()
        self.SetTopWindow(f)
        return True

class MainApplication(wx.App):
    
    def OnInit(self):
        
        f = MainFrame(None)
        f.Show()
        return True

class PeriodicTableViewerApp(wx.App):
    
    def OnInit(self):
        
        f = PeriodicTableViewer(None)
        f.Show()
        self.SetTopWindow(f)
        return True

class PlotterApp(wx.App):
    
    def OnInit(self):
        
        f = PlotterFrame(None)
        f.Show()
        return True
    
class UserDefinitionViewerApp(wx.App):  
      
    def OnInit(self):
        
        f = UserDefinitionViewer(None)
        self.SetTopWindow(f)
        f.Show()
        return True
    

