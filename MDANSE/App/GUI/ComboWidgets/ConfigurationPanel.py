import wx

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError

class ConfigurationPanel(wx.Panel):
    
    def __init__(self, parent, configuration):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self._configuration = configuration
        
        self._widgets = {}
        
        self.build_panel()
        
    def build_panel(self):
        
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)

        for cfg in self._configuration.configurators.values():

            widgetClass = REGISTRY["configurator_widget"][cfg.widget]
                        
            self._widgets[cfg.name] = widgetClass(self, cfg.name, self._configuration)
            
            self.panelSizer.Add(self._widgets[cfg.name], 0, wx.ALL|wx.EXPAND, 5)
                  
        self.SetSizer(self.panelSizer)
                                   
        self.Layout()

        self.Fit()
                    
    @property
    def widgets(self):
        return self._widgets
                 
    def get_value(self):
        
        return dict([(k,v.get_value()) for k,v in self._widgets.items()])
    
    def validate(self):

        for w in self._widgets.values():
            w.SetBackgroundColour(wx.NullColour)
            w.Refresh()
             
        try:
            self._configuration.parameters = self.get_value()
        except ConfiguratorError as e:
            d = wx.MessageDialog(self, str(e), style=wx.ICON_ERROR|wx.STAY_ON_TOP|wx.CENTRE)
            d.ShowModal()
            w = self._widgets[e.configurator.name]
            w.SetBackgroundColour("Pink")
            w.Refresh()
            w.SetFocus()
            return False
        else:
            return True
