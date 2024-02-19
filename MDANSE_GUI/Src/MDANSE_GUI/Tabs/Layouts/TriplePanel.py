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
from qtpy.QtWidgets import QWidget
from .DoublePanel import DoublePanel


class TriplePanel(DoublePanel):
    """The triple panel layout which has the data and visualiser
    panel on the left and another panel on the right."""

    def __init__(self, *args, **kwargs):
        right_panel = kwargs.pop("right_panel", None)
        super().__init__(*args, **kwargs)

        if right_panel is not None:
            self._rightlayout.addWidget(right_panel)

    def add_visualiser_side(self, visualiser_side: QWidget) -> None:
        """Overrides the double panel method so that the visualiser is
        placed on the left.

        Parameters
        ----------
        visualiser_side : QWidget
            A QWidget.
        """
        if visualiser_side is not None:
            self._leftlayout.addWidget(visualiser_side)
            self._visualiser = visualiser_side
