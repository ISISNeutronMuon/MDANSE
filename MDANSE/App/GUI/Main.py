import wx

from MDANSE.App.GUI.MainFrame import MainFrame
from MDANSE.App.GUI.Framework.Plugins.Plotter.PlotterPlugin import PlotterFrame
from MDANSE.App.GUI.Framework.Plugins.PeriodicTablePlugin import PeriodicTableFrame
from MDANSE.App.GUI.Framework.Plugins.UserDefinitionViewerPlugin import UserDefinitionViewerFrame

class MainApplication(wx.App):
    
    def OnInit(self):
        
        f = MainFrame(None)
        f.Show()
        self.SetTopWindow(f)
        return True

class PeriodicTableApplication(wx.App):
    
    def OnInit(self):
        
        f = PeriodicTableFrame(None)
        f.Show()
        self.SetTopWindow(f)
        return True

class PlotterApplication(wx.App):
    
    def OnInit(self):
        
        f = PlotterFrame(None)
        f.Show()
        self.SetTopWindow(f)
        return True
    
class UserDefinitionViewerApplication(wx.App):  
      
    def OnInit(self):
        
        f = UserDefinitionViewerFrame(None)
        f.Show()
        self.SetTopWindow(f)
        return True
    
if __name__ == "__main__":
    
    app = MainApplication()
    app.MainLoop()
    