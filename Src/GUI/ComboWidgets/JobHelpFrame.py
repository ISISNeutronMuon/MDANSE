# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/ComboWidgets/JobHelpFrame.py
# @brief     Implements module/class/test JobHelpFrame
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

import wx
import wx.html as wxhtml

from MDANSE import PLATFORM, REGISTRY

class JobHelpFrame(wx.Frame):
    
    def __init__(self, parent, job):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="About %s" % job.label, size =(800,600))
        
        self.nolog = wx.LogNull()

        moduleFullName = PLATFORM.full_dotted_module(job.__class__)
        
        if moduleFullName is None:
            self._doc = ""            
        else:
            self._doc = os.path.join(PLATFORM.help_path(), moduleFullName+'.html')
                                                                        
        self.build()
        
    def build(self):
        
        htmlPanel = wxhtml.HtmlWindow(self, wx.ID_ANY)
        htmlPanel.LoadPage(self._doc)

if __name__ == "__main__":
    app = wx.App(False)
    f = JobHelpFrame(None,REGISTRY['job']['msd']())
    f.Show()
    app.MainLoop()            
