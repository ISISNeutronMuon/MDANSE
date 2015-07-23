import wx.combo

class ComboCheckbox(wx.combo.ComboPopup):
    
    def __init__(self, items, maxNumberOfItems=None):
        
        wx.combo.ComboPopup.__init__(self)
        self._items = items
        self._maxNumberOfItems = maxNumberOfItems
        
    @property
    def items(self):
        return self._items

    @property
    def checklistbox(self):
        
        return self._checklistbox
        
    def Create(self, parent):    
        self._checklistbox = wx.CheckListBox(parent, -1, choices=self._items)
        self._checklistbox.Bind(wx.EVT_CHECKLISTBOX, self.on_check_item)
        if not self._checklistbox.IsEmpty():
            self._checklistbox.Check(0)
                
        return True
    
    def GetControl(self):
        return self._checklistbox
        
    def GetAdjustedSize(self, minWidth, prefHeight, maxHeight):
        return self._checklistbox.GetSize()
    
    def GetStringValue(self): 
        return self._checklistbox.GetCheckedStrings()
    
    def on_check_item(self, event):
        
        if self._maxNumberOfItems is None:
            return
                
        nCheckedItems = len(self._checklistbox.GetChecked())
        
        if nCheckedItems > self._maxNumberOfItems:
            self._checklistbox.Check(event.GetInt(), False)        