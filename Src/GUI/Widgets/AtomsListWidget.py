# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/AtomsListWidget.py
# @brief     Implements module/class/test AtomsListWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.GUI.Widgets.UserDefinitionWidget import UserDefinitionWidget, UserDefinitionDialog


class AtomListWidget(UserDefinitionWidget):
    
    def on_new_definition(self, event):

        dlg = UserDefinitionDialog(self, self._trajectory, self._type)

        dlg.plugin.set_natoms(self._configurator._nAtoms)

        dlg.plugin.enable_natoms_selection(False)
        
        dlg.ShowModal()
        
    def msg_set_ud(self, message):
         
        uds = UD_STORE.filter(self._basename, self._type)
                                
        uds = [v for v in uds if UD_STORE.get_definition(self._basename, self._type,v)["natoms"]==self._configurator._nAtoms]
        
        self._availableUDs.SetItems(uds)


REGISTRY["atoms_list"] = AtomListWidget
    
