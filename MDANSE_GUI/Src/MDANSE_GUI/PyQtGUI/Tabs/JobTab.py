# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/RegistryViewer.py
# @brief     Shows the MDANSE jobs. Can run standalone.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QPushButton, QTextEdit, QWidget, QFileDialog

from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.PyQtGUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.PyQtGUI.Session.LocalSession import LocalSession
from MDANSE_GUI.PyQtGUI.Widgets.ActionDialog import ActionDialog
from MDANSE_GUI.PyQtGUI.Tabs.Visualisers.TrajectoryInfo import TrajectoryInfo
from MDANSE_GUI.PyQtGUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.PyQtGUI.Tabs.Views.ActionsTree import ActionsTree


class JobTab(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = LocalSession()
        self._actions_holder = JobTree()
        self._actions_holder.populateTree()
        self._actions_list = ActionsTree()
        self._visualiser = TrajectoryInfo()
        self._core = DoublePanel(
            data_side=self._actions_list, visualiser_side=self._visualiser
        )
        self._core.set_model(self._actions_holder)
        self._core.set_label_text(
            """This is the list of jobs you can run using MDANSE.
Pick a job to see additional information.
Use the button to start a job.
        """
        )
        self._core.add_button("Show the job dialog!", self.show_action_dialog)

    @Slot()
    def show_action_dialog(self):
        dialog = ActionDialog
        current_item = self._core.current_item()
        if current_item is None:
            return
        converter = IJob.create(current_item.text())
        try:
            dialog_instance = dialog(
                self._core, converter=converter, source_object=self.current_object
            )
        except Exception as e:
            self._core.fail(repr(e))
        dialog_instance.new_thread_objects.connect(self.backend.job_holder.startThread)
        dialog_instance.show()
        try:
            result = dialog_instance.exec()
        except Exception as e:
            self._core.fail(repr(e))


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = JobTab(window)
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
