import wx

from MMTK.Trajectory import TrajectoryVariable

from MDANSE import REGISTRY

from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Widgets.IWidget import IWidget
                            
class TrajectoryVariableWidget(IWidget):
    
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._variable = wx.Choice(self._widgetPanel, wx.ID_ANY, choices=[])
                
        sizer.Add(self._variable, 1, wx.ALL|wx.EXPAND, 5)
        
        return sizer
        
    def get_widget_value(self):
        
        return self._variable.GetStringSelection()

    def set_data(self, datakey):


        trajectory = DATA_CONTROLLER[datakey].data
        self._variable.SetItems([v for v in trajectory.variables() if isinstance(getattr(trajectory,v),TrajectoryVariable)])
        self._variable.SetSelection(0)

REGISTRY["trajectory_variable"] = TrajectoryVariableWidget
