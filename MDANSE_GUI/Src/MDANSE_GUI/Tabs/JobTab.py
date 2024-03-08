# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE_GUI/Tabs/JobTab.py
# @brief     Shows the MDANSE jobs. Can run standalone.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
from functools import partial
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget, QComboBox

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.TriplePanel import TriplePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Visualisers.Action import Action
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
        self.action = kwargs.pop("action")
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

    def set_job_starter(self, job_starter):
        self._job_starter = job_starter
        self.action.new_thread_objects.connect(self._job_starter.startProcess)

    @Slot(str)
    def set_current_trajectory(self, new_name: str) -> None:
        self._current_trajectory = new_name

        traj_model = self._trajectory_combo.model()
        if traj_model.rowCount() < 1:
            # the combobox changed and there are no trajectories, they
            # were probably deleted lets clear the action widgets
            self.action.set_trajectory(path=None, trajectory=None)
            self.action.clear_panel()
            return

        node_number = traj_model.item(self._trajectory_combo.currentIndex(), 0).data()
        print(
            f"Combo model: node_number {node_number} found in item {self._trajectory_combo.currentText()}"
        )
        # The combobox was changed we need to update the action
        # widgets with the new trajectory
        self.action.set_trajectory(path=None, trajectory=traj_model._nodes[node_number][0])
        current_item = self._core.current_item()
        if current_item is not None:
            # we only update the widget if a job is selected from the
            # actions tree
            self.action.update_panel(current_item.text())

    @classmethod
    def standard_instance(cls):
        action = Action()
        the_tab = cls(
            window,
            name="AvailableJobs",
            model=JobTree(),
            view=ActionsTree(),
            visualiser=Action(),
            layout=partial(
                TriplePanel,
                left_panel=TextInfo(
                    header="MDANSE Analysis",
                    footer="Look up our Read The Docs page:"
                    + "https://mdanse.readthedocs.io/en/protos/",
                ),
            ),
            label_text=job_tab_label,
            action=action,
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
        action = Action()
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=kwargs.get("model", JobTree(filter="Analysis")),
            combo_model=kwargs.get("combo_model", None),
            view=ActionsTree(),
            visualiser=action,
            layout=partial(
                TriplePanel,
                left_panel=TextInfo(
                    header="MDANSE Analysis",
                    footer="Look up our "
                    + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                    + " page.",
                ),
            ),
            label_text=job_tab_label,
            action=action,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    action = Action()
    the_tab = JobTab(
        window,
        name="AvailableJobs",
        model=JobTree(),
        view=ActionsTree(),
        visualiser=action,
        layout=partial(
            TriplePanel,
            left_panel=TextInfo(
                header="MDANSE Analysis",
                footer="Look up our "
                + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                + " page.",
            ),
        ),
        label_text=job_tab_label,
        action=action,
    )
    the_tab.update_trajectory_list(["/Users/maciej.bartkowiak/an_example/BLAH.mdt"])
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
