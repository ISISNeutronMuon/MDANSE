# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/AtomTransmutationWidget.py
# @brief     Implements module/class/test AtomTransmutationWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

from MDANSE import REGISTRY
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.GUI.Widgets.AtomSelectionWidget import AtomSelectionWidget
from MDANSE.GUI.Icons import ICONS

class AtomTransmutationWidget(AtomSelectionWidget):
             
    udType = "atom_selection"
  
    def on_add_definition(self,event):
        
        panel = wx.Panel(self._widgetPanel,wx.ID_ANY)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
 
        availableUDs = wx.Choice(panel, wx.ID_ANY,style=wx.CB_SORT)
        uds = UD_STORE.filter(self._basename, "atom_selection")
        availableUDs.SetItems(uds)
         
        view = wx.Button(panel, wx.ID_ANY, label="View selected definition")
        elements = wx.ComboBox(panel, wx.ID_ANY, value="Transmutate to", choices=ATOMS_DATABASE.atoms)
        remove = wx.BitmapButton(panel, wx.ID_ANY, ICONS["minus",16,16])
 
        sizer.Add(availableUDs, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(view, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(elements, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(remove, 0, wx.ALL|wx.EXPAND, 5)
         
        panel.SetSizer(sizer)
         
        self._sizer.Add(panel,1,wx.ALL|wx.EXPAND,5)
         
        self._widgetPanel.GrandParent.Layout()
        self._widgetPanel.GrandParent.Refresh()

        self.Bind(wx.EVT_BUTTON, self.on_view_definition, view)
        self.Bind(wx.EVT_BUTTON, self.on_remove_definition, remove)
          
    def get_widget_value(self):

        sizerItemList = list(self._sizer.GetChildren())
        del sizerItemList[0]

        uds = []
        for sizerItem in sizerItemList:
            
            panel = sizerItem.GetWindow()
            children = panel.GetChildren()
            udName = children[0].GetStringSelection()
            element = children[2].GetStringSelection()
            
            if not element:
                raise ConfiguratorError("No target element provided for %r selection." % udName)

            uds.append([udName,element])
                  
        if not uds:
            return None
        else:
            return uds
        
REGISTRY["atom_transmutation"] = AtomTransmutationWidget
