# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Handlers/DialogHandler.py
# @brief     Implements module/class/test DialogHandler
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import logging

import wx

from MDANSE import REGISTRY
from MDANSE.Framework.Handlers.IHandler import IHandler


class DialogHandler(IHandler, logging.Handler):
    ICONS = {
        "DEBUG": wx.ICON_INFORMATION,
        "CRITICAL": wx.ICON_ERROR,
        "ERROR": wx.ICON_ERROR,
        "INFO": wx.ICON_INFORMATION,
        "WARNING": wx.ICON_WARNING,
    }

    def emit(self, record):
        icon = DialogHandler.ICONS[record.levelname]

        d = wx.MessageDialog(
            None, message=self.format(record), style=wx.OK | wx.STAY_ON_TOP | icon
        )

        d.ShowModal()


REGISTRY["dialog"] = DialogHandler
