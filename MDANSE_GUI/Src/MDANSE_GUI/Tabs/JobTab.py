#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from __future__ import annotations

import os
from functools import partial
from pathlib import PurePath

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QComboBox, QLabel, QWidget

from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.MoleculeWidget import MoleculeWidget
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.MultiPanel import MultiPanel
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Views.ActionsTree import ActionsTree
from MDANSE_GUI.Tabs.Visualisers.Action import Action
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo

job_tab_label = """This is the list of <b>analysis tasks</b>
you can run using MDANSE.
Pick an analysis name to see additional information.
<br><br>
Use a button at the bottom of the panel to start an analysis run,
or to save the inputs as a script.
<br><br>
If you regularly use specific <b>resolution settings</b> or
<b>Q vector generation parameters</b>, you can save them in
the instrument tab as an instrument profile, and use them
in your analysis by setting the "instrument" name to the
one you defined. The parameters saved under the instrument name
will be used as initial values when you switch to a new analysis type.
"""


class JobTab(GeneralTab):
    """The tab for choosing and starting a new job."""

    def __init__(
        self, *args, action=None, combo_model=None, instrument_model=None, **kwargs
    ):
        self._needs_updating = False
        self.action = action

        super().__init__(*args, **kwargs)

        self._current_trajectory = ""
        self._current_trajectory_index = -1
        self._job_starter = None
        self._own_index = -1
        self._instrument_index = -1
        self._trajectory_combo = QComboBox()
        self._trajectory_combo.setEditable(False)
        self._trajectory_combo.currentIndexChanged.connect(self.set_current_trajectory)
        if combo_model is not None:
            self._trajectory_combo.setModel(combo_model)
        combo_model.finished_loading.connect(self.reload_trajectory)
        self._instrument_combo = QComboBox()
        self._instrument_combo.setEditable(False)
        self._instrument_combo.currentIndexChanged.connect(self.set_current_instrument)

        if instrument_model is not None:
            self._instrument_combo.setModel(instrument_model)

        self._core.add_widget(QLabel("Trajectory:"))
        self._core.add_widget(self._trajectory_combo)
        self._core.add_widget(QLabel("Instrument:"), upper=False)
        self._core.add_widget(self._instrument_combo, upper=False)

        self.action._parent_tab = self
        self._visualiser._parent_tab = self

    def set_own_index(self, index: int):
        self._own_index = index

    def set_job_starter(self, job_starter):
        self._job_starter = job_starter
        self.action.new_thread_objects.connect(self._job_starter.startProcess)
        self.action.run_and_load.connect(self._job_starter.startProcessAndLoad)

    def grouped_settings(self):
        return super().grouped_settings() | {
            "Execution": (
                {"auto-load": "True"},
                {
                    "auto-load": "Unless manually switched off, the GUI will try to load the job results when the job is finished."
                },
            ),
        }

    @Slot(int)
    def reload_trajectory(self, node_number: int) -> None:
        if node_number != self._current_trajectory_index:
            return
        self.set_trajectory_from_node_number(node_number)

    @Slot(int)
    def set_current_trajectory(self, index: int) -> None:
        self._current_trajectory = self._trajectory_combo.currentText()

        traj_model = self._trajectory_combo.model()
        if traj_model.rowCount() < 1:
            # the combobox changed and there are no trajectories, they
            # were probably deleted lets clear the action widgets
            self.action.set_trajectory(trajectory=None)
            self.action.clear_panel()
            return
        node_number = traj_model.item(index, 0).data()
        self.set_trajectory_from_node_number(node_number)

    def set_trajectory_from_node_number(self, node_number: int):
        traj_model = self._trajectory_combo.model()
        self._current_trajectory_index = node_number
        LOG.info(
            f"Combo model: node_number {node_number} found in item {self._current_trajectory}"
        )
        # The combobox was changed we need to update the action
        # widgets with the new trajectory
        traj_instance = traj_model.get_trajectory(node_number)
        if traj_instance is None or isinstance(traj_instance, str):
            return
        self.action.set_trajectory(trajectory=traj_instance)
        current_item = self._core.current_item()
        if current_item is not None:
            # we only update the widget if a job is selected from the
            # actions tree
            self.action.update_panel(current_item.text())

    @Slot(int)
    def set_current_instrument(self, index: int):
        LOG.debug(f"Switched instrument to {index}")
        instrument_model = self._instrument_combo.model()
        self.action.set_instrument(instrument_model._nodes[index])
        self._instrument_index = index
        current_item = self._core.current_item()
        if current_item is not None:
            # we only update the widget if a job is selected from the
            # actions tree
            self.action.apply_instrument()

    @Slot(int)
    def update_action_after_instrument_change(self, index: int):
        if index != self._instrument_index:
            return
        self._needs_updating = True

    @Slot(int)
    def update_action_on_tab_activation(self, current_index: int):
        if current_index != self._own_index:
            return
        self.action.test_file_outputs()
        if self._needs_updating:
            current_item = self._core.current_item()
            if current_item is not None:
                self.action.apply_instrument()
            self._needs_updating = False

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
                MultiPanel,
                left_panels=[
                    TextInfo(
                        header="MDANSE Analysis",
                        footer="Look up our Read The Docs page:"
                        + "https://mdanse.readthedocs.io/en/protos/",
                    )
                ],
            ),
            label_text=job_tab_label,
            action=action,
        )
        action._parent_tab = the_tab
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
        action = Action(use_preview=True)
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=kwargs.get("model", JobTree(filter="Converters")),
            combo_model=kwargs.get("combo_model", None),
            instrument_model=kwargs.get("instrument_model", None),
            view=ActionsTree(),
            visualiser=action,
            layout=partial(
                MultiPanel,
                left_panels=[
                    TextInfo(
                        header="MDANSE Analysis",
                        footer="Look up our "
                        + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                        + " page.",
                    )
                ],
            ),
            label_text=job_tab_label,
            action=action,
        )
        action.set_settings(the_tab._settings)
        the_tab._view.expand(the_tab._model.index(0, 0))
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
            MultiPanel,
            left_panels=[
                TextInfo(
                    header="MDANSE Analysis",
                    footer="Look up our "
                    + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                    + " page.",
                )
            ],
        ),
        label_text=job_tab_label,
        action=action,
    )
    the_tab.update_trajectory_list(["/Users/maciej.bartkowiak/an_example/BLAH.mdt"])
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
