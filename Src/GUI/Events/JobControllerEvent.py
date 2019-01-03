# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Events/JobControllerEvent.py
# @brief     Implements module/class/test JobControllerEvent
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

EVT_JOB_CONTROLLER_ID = wx.NewId()
EVT_JOB_CRASH_ID = wx.NewId()

def EVT_JOB_CONTROLLER(win, func):

    win.Connect(-1, -1, EVT_JOB_CONTROLLER_ID, func)

def EVT_JOB_CRASH(win, func):

    win.Connect(-1, -1, EVT_JOB_CRASH_ID, func)

class JobControllerEvent(wx.PyEvent):

    def __init__(self, runningJobs):

        wx.PyEvent.__init__(self)
        
        self.SetEventType(EVT_JOB_CONTROLLER_ID)
        
        self.runningJobs = runningJobs

class JobCrashEvent(wx.PyEvent):

    def __init__(self, traceback):

        wx.PyEvent.__init__(self)
        
        self.SetEventType(EVT_JOB_CRASH_ID)
        
        self.traceback = traceback
        