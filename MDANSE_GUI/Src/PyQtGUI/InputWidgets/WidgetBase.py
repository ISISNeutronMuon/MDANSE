# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtCore import QObject
from qtpy.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QVBoxLayout,
    QGridLayout,
)


class WidgetBase(QObject):
    def __init__(self, *args, **kwargs):
        parent = kwargs.get("parent", None)
        super().__init__(*args, parent=parent)
        label_text = kwargs.get("label", "")
        tooltip_text = kwargs.get("tooltip", "")
        base_type = kwargs.get("base_type", "QGroupBox")
        layout_type = kwargs.get("layout_type", "QHBoxLayout")
        if layout_type == "QHBoxLayout":
            layoutClass = QHBoxLayout
        elif layout_type == "QVBoxLayout":
            layoutClass = QVBoxLayout
        else:
            layoutClass = QGridLayout
        if base_type == "QWidget":
            base = QWidget(parent)
            layout = layoutClass(base)
            base.setLayout(layout)
            label = QLabel(label_text, base)
            layout.addWidget(label)
        elif base_type == "QGroupBox":
            base = QGroupBox(label_text)
            base.setToolTip(tooltip_text)
            layout = layoutClass(base)
            base.setLayout(layout)
        self._base = base
        self._layout = layout
        self._tooltip = tooltip_text
