# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/VectorWidget.py
# @brief     Implements module/class/test VectorWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QLineEdit, QLabel

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class VectorWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._changing_label = QLabel("Vector", parent=self._base)
        self._layout.addWidget(self._changing_label)
        vfields = []
        for val in ["0", "0", "1"]:
            temp = QLineEdit(val, self._base)
            self._layout.addWidget(temp)
            vfields.append(temp)
        self._vector_fields = vfields
        self._mode = 0
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The spatial properties in the analysis can be projected on a plane or on an axis, as chosen here."
        for wid in vfields:
            wid.setToolTip(tooltip_text)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        try:
            vector = [float(x.text()) for x in self._vector_fields]
        except:
            vector = [0, 0, 0]
        return vector
