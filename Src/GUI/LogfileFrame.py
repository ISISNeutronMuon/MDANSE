import os

import wx

from MDANSE import PLATFORM

class LogfileFrame(wx.Frame):
    
    def __init__(self,parent,jobName,*args,**kwargs):
        
        wx.Frame.__init__(self,parent,size=(800,500),*args,**kwargs)
        
        self._logfile = os.path.join(PLATFORM.logfiles_directory(),jobName)+'.txt'
        
        panel = wx.Panel(self,wx.ID_ANY)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._logFileContents = wx.TextCtrl(panel,wx.ID_ANY,style=wx.TE_AUTO_SCROLL|wx.TE_READONLY|wx.TE_MULTILINE)
        
        updateButton = wx.Button(panel,wx.ID_ANY,label="Update")
        
        sizer.Add(self._logFileContents,1,wx.ALL|wx.EXPAND,5)
        sizer.Add(updateButton,0,wx.ALL|wx.EXPAND,5)
        
        panel.SetSizer(sizer)
        
        self.update()
                
        self.Bind(wx.EVT_BUTTON,self.on_update,updateButton)
        
    def update(self):
        
        try:
            f = open(self._logfile,"r")
        except IOError:
            self._logFileContents.SetValue("Error opening %r file." % self._logfile)
        else:
            self._logFileContents.SetValue(f.read())
            
    def on_update(self,event):
        
        self.update()
