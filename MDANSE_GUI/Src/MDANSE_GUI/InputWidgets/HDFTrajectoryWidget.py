# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE_GUI/InputWidgets/HDFTrajectoryWidget.py
# @brief     Implements module/class/test HDFTrajectoryWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
import os

from qtpy.QtWidgets import QLabel

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class HDFTrajectoryWidget(WidgetBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        source_object = kwargs.get("source_object", None)
        try:
            filename = source_object
        except AttributeError:
            filename = None
        if filename is not None:
            label = QLabel(filename, self._base)
            self._layout.addWidget(label)
            trajectory_path, _ = os.path.split(filename)
            self.default_path = trajectory_path
        else:
            label = QLabel("No Trajectory available", self._base)
            self._layout.addWidget(label)
        self.default_labels()
        self.update_labels()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A single logical value that can be True of False"
        label.setToolTip(tooltip_text)

    def configure_using_default(self):
        """This is too static to have a default value"""

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "HDFTrajectoryWidget"
        if self._tooltip == "":
            self._tooltip = "The input trajectory to be processed"

    def get_value(self):
        return self.default_path

    def get_widget_value(self):
        return self.get_value()
