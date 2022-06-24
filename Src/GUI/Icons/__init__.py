# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Icons/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os
import sys

import wx

from MDANSE.Core.Singleton import Singleton

class Icons(object):
    
    __metaclass__ = Singleton
        
    def __getitem__(self,item):

        name, width, height = item

        icon = os.path.join(os.path.dirname(__file__),name+".png")

        image = wx.ImageFromBitmap(wx.Bitmap(icon))
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        
        return wx.BitmapFromImage(image)

    def add_icon(self,name,path):
        
        self._icons[name] = path
        
ICONS = Icons()     
