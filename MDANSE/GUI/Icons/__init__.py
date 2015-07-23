import os

import wx

from MDANSE.Core.Singleton import Singleton

root = os.path.dirname(__file__)

class Icons(object):
    
    __metaclass__ = Singleton
        
    def __getitem__(self,item):

        name, width, height = item

        icon = os.path.join(root,name)+".png"

        image = wx.ImageFromBitmap(wx.Bitmap(icon))
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        
        return wx.BitmapFromImage(image)

    def add_icon(self,name,path):
        
        self._icons[name] = path
        
ICONS = Icons()     
