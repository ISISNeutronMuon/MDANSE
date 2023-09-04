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

import wx


class ComboCheckbox(wx.ComboPopup):
    def __init__(self, items, maxNumberOfItems=None):
        wx.ComboPopup.__init__(self)

        self._items = items
        self._maxNumberOfItems = maxNumberOfItems
        self._currentItem = -1

    def OnMotion(self, event):
        item = self._checkboxListCtrl.HitTest(event.GetPosition())
        if item >= 0:
            self._checkboxListCtrl.Select(item)
            self._currentItem = item

    def Create(self, parent):
        self._checkboxListCtrl = wx.CheckListBox(parent, wx.ID_ANY, choices=self._items)
        self._checkboxListCtrl.Bind(wx.EVT_MOTION, self.OnMotion)
        self._checkboxListCtrl.Bind(wx.EVT_LEFT_DOWN, self.on_check_item)

        return True

    def GetControl(self):
        return self._checkboxListCtrl

    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        size = self.GetControl().GetSize()
        return wx.Size(minWidth, size[1])

    def GetStringValue(self):
        return self.GetCheckedStrings()

    def on_check_item(self, event):
        # Control only if ele;ent is checked
        if not self._checkboxListCtrl.IsChecked(self._currentItem):
            # Control max number of items
            if self._maxNumberOfItems is None:
                # Accept the event
                self._checkboxListCtrl.Check(self._currentItem, True)
            else:
                # Control the number of checked items
                nCheckedItems = len(self._checkboxListCtrl.GetChecked())
                if nCheckedItems < self._maxNumberOfItems:
                    # Chech the item
                    self._checkboxListCtrl.Check(self._currentItem, True)
        else:
            self._checkboxListCtrl.Check(self._currentItem, False)
