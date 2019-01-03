import wx

from MDANSE import REGISTRY
from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Widgets.IWidget import IWidget

class InterpolationOrderWidget(IWidget):
    
    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="interpolation order")
        
        self._interpolationOrder = wx.Choice(self._widgetPanel, wx.ID_ANY)
                
        sizer.Add(label, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)
        sizer.Add(self._interpolationOrder, 0, wx.ALL, 5)
                                
        return sizer
                                                            
    def set_data(self, datakey):                

        trajectory = DATA_CONTROLLER[datakey]
                
        if "velocities" in trajectory.data.variables():
            self._interpolationOrder.SetItems(self._configurator.choices)
        else:
            self._interpolationOrder.SetItems(self._configurator.choices[1:])
            
        self._interpolationOrder.SetStringSelection(self._configurator.choices[0])
                    
    def get_widget_value(self):
             
        value = self._interpolationOrder.GetStringSelection()
        
        return value

REGISTRY["interpolation_order"] = InterpolationOrderWidget
