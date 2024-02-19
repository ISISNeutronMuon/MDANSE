# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE_GUI/Tabs/Layouts/TriplePanel.py
# @brief     Base widget for the MDANSE GUI
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************
from .DoublePanel import DoublePanel


class TriplePanel(DoublePanel):
    """The triple panel layout which adds an extra visualiser panel to
    the left side of the layout"""

    def __init__(self, *args, **kwargs):
        left_panel = kwargs.pop("left_panel", None)
        super().__init__(*args, **kwargs)

        if left_panel is not None:
            self._leftlayout.addWidget(left_panel)
            if self._view is not None:
                self._view.connect_to_visualiser(left_panel)
