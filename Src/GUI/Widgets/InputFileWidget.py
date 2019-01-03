import wx
import wx.lib.filebrowsebutton as wxfile

from MDANSE import REGISTRY
from MDANSE.Framework.Configurable import ConfigurationError
from MDANSE.GUI.Widgets.IWidget import IWidget

class InputFileWidget(IWidget):
        
    def add_widgets(self):
        
        default = self._configurator.default
        wildcard = self._configurator.wildcard

        sizer = wx.BoxSizer(wx.VERTICAL)
                
        self._browser = wxfile.FileBrowseButton(self._widgetPanel, wx.ID_ANY, labelText="", initialValue=default, startDirectory=default,fileMask=wildcard)

        sizer.Add(self._browser, 1, wx.ALL|wx.EXPAND, 5)

        return sizer
        
    def get_widget_value(self):

        filename = self._browser.GetValue()

        if not filename:
            raise ConfigurationError("No input file selected", self)

        return filename
    
REGISTRY["input_file"] = InputFileWidget
