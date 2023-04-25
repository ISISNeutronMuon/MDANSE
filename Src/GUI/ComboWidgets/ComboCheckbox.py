# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/ComboWidgets/ComboCheckbox.py
# @brief     Implements module/class/test ComboCheckbox
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx.combo

class ComboCheckbox(wx.CheckListBox,wx.combo.ComboPopup):
    
    def __init__(self, items, maxNumberOfItems=None):
                
        self.PostCreate(wx.PreCheckListBox())
        
        wx.combo.ComboPopup.__init__(self)
        
        self._items = items
        self._maxNumberOfItems = maxNumberOfItems
        self._currentItem = -1
                        
    @property
    def items(self):
        return self._items

    @property
    def checklistbox(self):
        
        return self

    def OnMotion(self, event):
        
        item  = self.HitTest(event.GetPosition())
        if item >= 0:
            self.Select(item)
            self._currentItem = item
        
    def Create(self, parent): 

        wx.CheckListBox.Create(self,parent, -1, choices=self._items)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_check_item)
        if not self.IsEmpty():
            self.Check(0)
                
        return True
    
    def GetControl(self):
        return self
            
    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
         size = self.GetControl().GetSize()
         return wx.Size(minWidth, size[1])

    def GetStringValue(self): 
        return self.GetCheckedStrings()
    
    def on_check_item(self, event):
            
        # Control only if ele;ent is checked
        if not self.IsChecked(self._currentItem):

            # Control max number of items
            if self._maxNumberOfItems is None:
                # Accept the event
                self.Check(self._currentItem, True)        
            else:
                # Control the number of checked items
                nCheckedItems = len(self.GetChecked())
                if nCheckedItems < self._maxNumberOfItems:
                    # Chech the item
                    self.Check(self._currentItem, True)
        else:
            self.Check(self._currentItem, False)
