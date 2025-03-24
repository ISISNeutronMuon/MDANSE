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
import os
from functools import partial
from pathlib import PurePath

from MDANSE import PLATFORM
from MDANSE.Framework.AtomSelector import SelectionStorage
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.MLogging import LOG
from qtpy.QtCore import QSortFilterProxyModel, Slot
from qtpy.QtWidgets import QComboBox, QLabel, QTableView, QWidget

from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewerWithPicking
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.MultiPanel import MultiPanel
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Views.InstrumentList import InstrumentList
from MDANSE_GUI.Tabs.Visualisers.InstrumentDetails import InstrumentDetails
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Visualisers.View3D import View3D

label_text = """Browse through the saved atom selection definitions,
and preview what they will select in the current trajectory.
"""


class SelectionTab(GeneralTab):
    """Tab for visualising different atom selections."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        trajectory_model = kwargs.get("trajectory_model")
        self._trajectory_combo = QComboBox()
        self._trajectory_combo.setEditable(False)
        self._trajectory_combo.currentIndexChanged.connect(self.set_current_trajectory)
        if trajectory_model is not None:
            self._trajectory_combo.setModel(trajectory_model)
        selection_model = kwargs.get("selection_model")
        if selection_model is None:
            selection_model = SelectionStorage()
        self._view.setModel(selection_model)
        self._core.add_widget(QLabel("Trajectory:"))
        self._core.add_widget(self._trajectory_combo)
        self._core.add_button("Load from MDA", self._view.add_instrument)
        self._core.add_button("Save Selections", self._view.save_to_file, upper=False)

    @Slot(int)
    def set_current_trajectory(self, index: int) -> None:
        """Pass the trajectory from combo to 3D view.

        Parameters
        ----------
        index : int
            model index of the trajectory

        """
        self._current_trajectory = self._trajectory_combo.currentText()
        traj_model = self._trajectory_combo.model()
        node_number = traj_model.item(index, 0).data()
        traj_instance = traj_model._nodes[node_number]
        self._visualiser.update_panel((self._current_trajectory, traj_instance))

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="Instruments",
            session=LocalSession(),
            model=GeneralModel(),
            view=QTableView(),
            visualiser=View3D(MolecularViewerWithPicking()),
            layout=partial(MultiPanel, left_panels=[TextInfo()]),
            label_text=label_text,
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
            model=kwargs.get("model", GeneralModel()),
            view=QTableView(),
            visualiser=View3D(MolecularViewerWithPicking()),
            layout=partial(MultiPanel, left_panels=[TextInfo()]),
            label_text=label_text,
        )
        return the_tab


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = SelectionTab.standard_instance()
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
