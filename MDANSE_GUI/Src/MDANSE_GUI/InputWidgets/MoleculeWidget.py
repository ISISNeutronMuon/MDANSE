# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/MoleculeWidget.py
# @brief     Implements module/class/test MoleculeWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QComboBox

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class MoleculeWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configurator = kwargs.get("configurator", None)
        trajectory_configurator = kwargs.get("trajectory_configurator", None)
        default_option = ""
        if trajectory_configurator is not None:
            option_list = trajectory_configurator[
                "instance"
            ].chemical_system.unique_molecules()
            if len(option_list) > 0:
                default_option = option_list[0]
        else:
            if configurator is None:
                option_list = kwargs.get("choices", [])
            else:
                option_list = configurator.choices
                default_option = configurator.default
        field = QComboBox(self._base)
        field.addItems(option_list)
        field.setCurrentText(default_option)
        field.currentTextChanged.connect(self.updateValue)
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = (
                "A single option can be picked out of all the options listed."
            )
        field.setToolTip(tooltip_text)
        self._field = field
        self._layout.addWidget(field)
        self._configurator = configurator
        self.default_labels()
        self.update_labels()
        self.updateValue()

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
