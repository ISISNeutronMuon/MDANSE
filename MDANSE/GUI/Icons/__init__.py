import os
import pkg_resources
import sys

import wx

from MDANSE.Core.Singleton import Singleton

class Icons(object):
    
    __metaclass__ = Singleton
        
    def __getitem__(self,item):

        name, width, height = item

        try:  
            icon = pkg_resources.resource_filename(__name__,name+".png")
        except:  
            if hasattr(sys,'frozen'):
                icon = os.path.join(os.path.dirname(sys.executable),name+".png")
            else:
                raise

        image = wx.ImageFromBitmap(wx.Bitmap(icon))
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        
        return wx.BitmapFromImage(image)

    def add_icon(self,name,path):
        
        self._icons[name] = path
        
ICONS = Icons()     
