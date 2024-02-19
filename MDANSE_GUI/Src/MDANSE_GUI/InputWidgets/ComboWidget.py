# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/SingleChoiceWidget.py
# @brief     Implements module/class/test SingleChoiceWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QComboBox
from qtpy.QtCore import Slot

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class ComboWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configurator = kwargs.get("configurator", None)
        if configurator is None:
            option_list = kwargs.get("choices", [])
        else:
            option_list = configurator.choices
            default_option = configurator.default
        field = QComboBox(self._base)
        field.addItems(option_list)
        field.setCurrentText(default_option)
        field.currentTextChanged.connect(self.updateValue)
        field.setToolTip(self._tooltip)
        self._field = field
        self._layout.addWidget(field)
        self._configurator = configurator
        self.default_labels()
        self.update_labels()

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "ComboWidget"
        if self._tooltip == "":
            self._tooltip = "You only have one option. Choose wisely."

    def get_widget_value(self):
        return self._field.currentText()
