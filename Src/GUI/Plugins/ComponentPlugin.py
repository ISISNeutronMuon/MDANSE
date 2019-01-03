from MDANSE.GUI.Plugins.IPlugin import IPlugin 
             
class ComponentPlugin(IPlugin):
    
    @property
    def datakey(self):
        return self.parent.datakey

    @property
    def dataproxy(self):
        return self.parent.dataproxy
    
    @property
    def dataplugin(self):
        return self.parent.dataplugin

