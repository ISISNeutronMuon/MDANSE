# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/PythonObjectWidgets.py
# @brief     Implements module/class/test PythonObjectWidgets
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import ast

import wx

from MDANSE import REGISTRY

from MDANSE.GUI.Widgets.IWidget import IWidget

class PythonObjectWidget(IWidget):
    
    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._string = wx.TextCtrl(self._widgetPanel, wx.ID_ANY, value=repr(self._configurator.default))

        sizer.Add(self._string, 1, wx.ALL|wx.EXPAND, 5)

        return sizer
            
    def get_widget_value(self):
                
        val = self._string.GetValue()

        return ast.literal_eval(val)

REGISTRY["python_object"] = PythonObjectWidget
