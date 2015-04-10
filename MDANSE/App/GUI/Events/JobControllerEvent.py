import wx

EVT_JOB_CONTROLLER_ID = wx.NewId()

def EVT_JOB_CONTROLLER(win, func):

    win.Connect(-1, -1, EVT_JOB_CONTROLLER_ID, func)

class JobControllerEvent(wx.PyEvent):

    def __init__(self, registry):

        wx.PyEvent.__init__(self)
        
        self.SetEventType(EVT_JOB_CONTROLLER_ID)
        
        self.registry = registry
        