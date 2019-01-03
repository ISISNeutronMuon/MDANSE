import wx

from MMTK.Trajectory import Trajectory

from MDANSE import REGISTRY
from MDANSE.Framework.Configurable import ConfigurationError

from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Widgets.IWidget import IWidget

class MMTKTrajectoryWidget(IWidget):
            
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._trajectory = wx.StaticText(self._widgetPanel, wx.ID_ANY)

        sizer.Add(self._trajectory, 1, wx.ALL|wx.EXPAND, 5)
                        
        return sizer
            
    def set_data(self, datakey):
                        
        data = DATA_CONTROLLER[datakey].data
        
        if not isinstance(data, Trajectory):
            return

        self._trajectory.SetLabel(datakey)
                        
    def get_widget_value(self):
        
        filename = self._trajectory.GetLabelText()
        
        if not filename:
            raise ConfigurationError("No MMTK trajectory file selected", self)
        
        return filename
    
REGISTRY["mmtk_trajectory"] = MMTKTrajectoryWidget
