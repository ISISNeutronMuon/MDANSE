# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/PartialChargesWidget.py
# @brief     Implements module/class/test PartialChargesWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

import wx

from MDANSE import REGISTRY

from MDANSE.GUI.Widgets.UserDefinitionWidget import (
    UserDefinitionDialog,
    UserDefinitionWidget,
)


class PartialChargesWidget(UserDefinitionWidget):
    pass


REGISTRY["partial_charges"] = PartialChargesWidget

if __name__ == "__main__":
    from MDANSE import PLATFORM
    from MDANSE.MolecularDynamics.Trajectory import Trajectory

    t = Trajectory(
        os.path.join(
            PLATFORM.example_data_directory(), "Trajectories", "HDF", "waterbox.h5"
        )
    )

    app = wx.App(False)

    p = UserDefinitionDialog(None, t, "partial_charges")

    p.SetSize((800, 800))

    p.ShowModal()

    p.Destroy()

    app.MainLoop()