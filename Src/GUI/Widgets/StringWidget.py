import wx

from MDANSE import REGISTRY

from MDANSE.GUI.Widgets.IWidget import IWidget

class StringWidget(IWidget):

    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._string = wx.TextCtrl(self._widgetPanel, wx.ID_ANY, value=self._configurator.default)

        sizer.Add(self._string, 0, wx.ALL, 5)

        return sizer
            
    def get_widget_value(self):
                
        val = self._string.GetValue()

        return val

REGISTRY["string"] = StringWidget
