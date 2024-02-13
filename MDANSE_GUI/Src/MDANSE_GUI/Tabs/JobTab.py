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


from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtGui import QStandardItem
from qtpy.QtWidgets import QWidget, QComboBox

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Widgets.ActionDialog import ActionDialog
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Views.ActionsTree import ActionsTree


job_tab_label = """This is the list of jobs you can run using MDANSE.
Pick a job to see additional information.
Use the button to start a job.
"""


class JobTab(GeneralTab):
    """The tab for choosing and starting a new job."""

    def __init__(self, *args, **kwargs):
        cmodel = kwargs.pop("combo_model", None)
        super().__init__(*args, **kwargs)
        self._current_trajectory = ""
        self._job_starter = None
        self._trajectory_combo = QComboBox()
        self._trajectory_combo.setEditable(False)
        self._trajectory_combo.currentTextChanged.connect(self.set_current_trajectory)
        if cmodel is not None:
            self._trajectory_combo.setModel(cmodel)
        self._core.add_widget(self._trajectory_combo)
        self._core.add_button("Show the job dialog!", self.show_action_dialog)

    def set_job_starter(self, job_starter):
        self._job_starter = job_starter

    @Slot(str)
    def set_current_trajectory(self, new_name: str):
        self._current_trajectory = new_name

    @Slot()
    def show_action_dialog(self):
        dialog = ActionDialog
        current_item = self._core.current_item()
        traj_model = self._trajectory_combo.model()
        if traj_model.rowCount() < 1:
            return
        # node_number = self._trajectory_combo.currentData()
        node_number = traj_model.item(self._trajectory_combo.currentIndex(), 0).data()
        print(
            f"Combo model: node_number {node_number} found in item {self._trajectory_combo.currentText()}"
        )
        self._current_trajectory = traj_model._nodes[node_number]
        print(f"Current trajectory is {self._current_trajectory}")
        if current_item is None:
            return
        try:
            converter = IJob.create(current_item.text())
        except ValueError as e:
            print(f"Failed: {e}")
            return
        except IndexError as e:
            print(f"Failed: {e}")
            return
        dialog_instance = dialog(
            self._core,
            job_name=current_item.text(),
            trajectory=self._current_trajectory,
        )
        # except Exception as e:
        #     self.error(repr(e))
        if self._job_starter is not None:
            dialog_instance.new_thread_objects.connect(self._job_starter.startThread)
        dialog_instance.show()
        try:
            result = dialog_instance.exec()
        except Exception as e:
            self.error(repr(e))

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="AvailableJobs",
            model=JobTree(),
            view=ActionsTree(),
            visualiser=TextInfo(
                header="MDANSE Analysis",
                footer="Look up our Read The Docs page:"
                + "https://mdanse.readthedocs.io/en/protos/",
            ),
            layout=DoublePanel,
            label_text=job_tab_label,
        )
        return the_tab

    @classmethod
    def gui_instance(
        cls,
        parent: QWidget,
        name: str,
        session: LocalSession,
        settings,
        logger,
        **kwargs,
    ):
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=kwargs.get("model", JobTree()),
            combo_model=kwargs.get("combo_model", None),
            view=ActionsTree(),
            visualiser=TextInfo(
                header="MDANSE Analysis",
                footer="Look up our "
                + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                + " page.",
            ),
            layout=DoublePanel,
            label_text=job_tab_label,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = JobTab(
        window,
        name="AvailableJobs",
        model=JobTree(),
        view=ActionsTree(),
        visualiser=TextInfo(
            header="MDANSE Analysis",
            footer="Look up our "
            + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
            + " page.",
        ),
        layout=DoublePanel,
        label_text=job_tab_label,
    )
    the_tab.update_trajectory_list(["/Users/maciej.bartkowiak/an_example/BLAH.mdt"])
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
