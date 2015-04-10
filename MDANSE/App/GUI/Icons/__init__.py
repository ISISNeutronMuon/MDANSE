import os

import wx

from MDANSE.Core.Singleton import Singleton

root = os.path.dirname(__file__)

class Icons(object):
    
    __metaclass__ = Singleton
    
    def __init__(self):
        
        self._icons = {}
    
    def __getitem__(self,item):
        
        name, width, height = item
        image = wx.ImageFromBitmap(wx.Bitmap(self._icons[name]))
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        
        return wx.BitmapFromImage(image)

    def add_icon(self,name,path):
        
        self._icons[name] = path
        
ICONS = Icons()     
ICONS.add_icon("about",os.path.join(root,'about.png'))
ICONS.add_icon("bug",os.path.join(root,'bug.png'))
ICONS.add_icon("clock",os.path.join(root,'clock.png'))
ICONS.add_icon("empty_data",os.path.join(root,'empty_data.png'))
ICONS.add_icon("first",os.path.join(root,'first.png'))
ICONS.add_icon("help",os.path.join(root,'help.png'))
ICONS.add_icon("hourglass",os.path.join(root,'hourglass.png'))
ICONS.add_icon("last",os.path.join(root,'last.png'))
ICONS.add_icon("load",os.path.join(root,'load.png'))
ICONS.add_icon("log",os.path.join(root,'log.png'))
ICONS.add_icon("mdanse",os.path.join(root,'mdanse.png'))
ICONS.add_icon("pause",os.path.join(root,'pause.png'))
ICONS.add_icon("periodic_table",os.path.join(root,'periodic_table.png'))
ICONS.add_icon("play",os.path.join(root,'play.png'))
ICONS.add_icon("plot",os.path.join(root,'plot.png'))
ICONS.add_icon("preferences",os.path.join(root,'preferences.png'))
ICONS.add_icon("quit",os.path.join(root,'quit.png'))
ICONS.add_icon("run",os.path.join(root,'run.png'))
ICONS.add_icon("stop",os.path.join(root,'stop.png'))
ICONS.add_icon("user",os.path.join(root,'user.png'))
ICONS.add_icon("web",os.path.join(root,'web.png'))
ICONS.add_icon("about",os.path.join(root,'about.png'))
ICONS.add_icon("working_directory",os.path.join(root,'working_directory.png'))
