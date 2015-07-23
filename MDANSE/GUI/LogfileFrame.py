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
Created on May 28, 2015

:author: Eric C. Pellegrini
'''

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
