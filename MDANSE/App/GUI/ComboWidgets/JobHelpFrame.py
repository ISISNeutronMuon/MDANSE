import os

import wx
import wx.html as wxhtml

from MDANSE import PLATFORM, REGISTRY

class JobHelpFrame(wx.Frame):
    
    def __init__(self, parent, job):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="About %s" % job.label, size =(800,600))
        
        self.nolog = wx.LogNull()
                
        fully_qualified_name = 'MDANSE.Framework.Jobs' + '.' + job.__class__.__name__
                
        self._doc =  PLATFORM.get_path(os.path.join(PLATFORM.help_path(), fully_qualified_name + '.html'))
        
        self.build()
        
    def build(self):
        
        htmlPanel = wxhtml.HtmlWindow(self, wx.ID_ANY)
        htmlPanel.LoadPage(self._doc)

if __name__ == "__main__":
    app = wx.App(False)
    f = JobHelpFrame(None,REGISTRY['job']['msd']())
    f.Show()
    app.MainLoop()            
