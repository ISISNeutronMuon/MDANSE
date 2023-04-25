# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/JobTemplateEditor.py
# @brief     Implements module/class/test JobTemplateEditor
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

from MDANSE import LOGGER

class JobTemplateEditor(wx.Dialog):
        
    def __init__(self,*args,**kwargs):
        """
        The constructor.
        """

        # The base class constructor
        wx.Dialog.__init__(self,*args,**kwargs)
        
        self.Center()
        
        panel = wx.Panel(self,wx.ID_ANY)
        
        staticLabel0 = wx.StaticText(panel, -1, "Enter property settings")
        
        subPanel = wx.Panel(panel,wx.ID_ANY)
        staticLabel1 = wx.StaticText(subPanel, wx.ID_ANY, "Short name")
        self._shortName = wx.TextCtrl(subPanel, wx.ID_ANY)        
        staticLabel2 = wx.StaticText(subPanel, wx.ID_ANY, "Class name")
        self._className = wx.TextCtrl(subPanel, id = wx.ID_ANY)
        
        staticLine = wx.StaticLine(self, wx.ID_ANY)

        buttonPanel = wx.Panel(self,wx.ID_ANY)
        cancelButton = wx.Button(buttonPanel, wx.ID_CANCEL, "Cancel")
        saveButton = wx.Button(buttonPanel, wx.ID_OK, "Save")
        saveButton.SetDefault()

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(staticLabel0, 0, wx.ALL|wx.ALIGN_LEFT, 5)
        subsizer = wx.GridBagSizer(5,5)
        subsizer.Add(staticLabel1,pos=(0,0),flag=wx.ALIGN_CENTER_VERTICAL)
        subsizer.Add(self._shortName   ,pos=(0,1),flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subsizer.Add(staticLabel2,pos=(1,0),flag=wx.ALIGN_CENTER_VERTICAL)
        subsizer.Add(self._className,pos=(1,1),flag=wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        subsizer.AddGrowableCol(1)
        subPanel.SetSizer(subsizer)
        panelSizer.Add(subPanel, 0, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(panelSizer)

        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(cancelButton)
        btnsizer.AddButton(saveButton)
        btnsizer.Realize()        
        buttonPanel.SetSizer(btnsizer)

        dlgsizer = wx.BoxSizer(wx.VERTICAL)
        dlgsizer.Add(panel, 1, wx.ALL|wx.EXPAND, 5)
        dlgsizer.Add(staticLine, 0, wx.ALL|wx.EXPAND, 5)
        dlgsizer.Add(buttonPanel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.EXPAND, 5)
        
        # Bind the top sizer to the dialog.
        self.SetSizer(dlgsizer)
        
        self.Bind(wx.EVT_BUTTON,self.on_save,saveButton)
        
    def on_save(self,event):
        
        shortName = str(self._shortName.GetValue()).strip()
        className = str(self._className.GetValue()).strip()
        
        if not shortName or not className:
            wx.MessageBox('You must provide a short name and a class name', 'Invalid input', wx.OK | wx.ICON_ERROR)
            return
                
        from MDANSE.Framework.Jobs.IJob import IJob        
        
        try:
            filename = IJob.save_template(shortName,className)
        except (IOError,KeyError) as e:
            LOGGER(str(e),'error',['console'])
            return
        
        LOGGER('Job template successfully saved to %r.' % filename,'info',['console'])                
        self.EndModal(wx.ID_OK)
                          
if __name__ == "__main__":
    app = wx.App(False)
    f = JobTemplateEditor(None)
    f.ShowModal()
    f.Destroy()
    app.MainLoop()        
    
    
