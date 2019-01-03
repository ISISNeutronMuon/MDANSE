import wx

from MDANSE import REGISTRY
from MDANSE.Framework.Configurable import ConfigurationError
from MDANSE.GUI.Widgets.StringWidget import StringWidget

class FloatWidget(StringWidget):
    
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._float = wx.TextCtrl(self._widgetPanel, wx.ID_ANY, value=str(self._configurator.default),style=wx.TE_PROCESS_ENTER)
        
        sizer.Add(self._float, 0, wx.ALL, 5)
        
        return sizer

    def get_widget_value(self):
                
        try:
            val = float(self._float.GetValue())            
        except ValueError:
            raise ConfigurationError("Invalid value for %r entry" % self.name)
        else:
            return val
        
    @property
    def widget(self):
        
        return self._float
    
REGISTRY["float"] = FloatWidget
