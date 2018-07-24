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
Created on Oct 12, 2015

:author: Eric C. Pellegrini
'''

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
    
    
