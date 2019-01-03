from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.GUI.Widgets.UserDefinitionWidget import UserDefinitionWidget, UserDefinitionDialog

class AtomListWidget(UserDefinitionWidget):
    
    def on_new_user_definition(self,event):

        dlg = UserDefinitionDialog(self,self._trajectory,self._type)
        
        dlg.plugin.set_natoms(self._configurator._nAtoms)
                
        dlg.plugin.enable_natoms_selection(False)
        
        dlg.ShowModal()
        
    def msg_set_ud(self, message=None):
         
        uds = UD_STORE.filter(self._basename, self._type)
                                
        uds = [v for v in uds if UD_STORE.get_definition(self._basename, self._type,v)["natoms"]==self._configurator._nAtoms] 
        
        self._availableUDs.SetItems(uds)

REGISTRY["atoms_list"] = AtomListWidget
    
