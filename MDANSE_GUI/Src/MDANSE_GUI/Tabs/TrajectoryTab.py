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

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget, QFileDialog

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.TriplePanel import TriplePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Views.TrajectoryView import TrajectoryView
from MDANSE_GUI.Tabs.Visualisers.TrajectoryInfo import TrajectoryInfo
from MDANSE_GUI.Tabs.Visualisers.View3D import View3D


label_text = """Here you can load the .mdt files.
They are MD trajectories in HDF5 format created by one of the MDANSE converters.
You can select trajectories. They will be visualised in the 3D view window.
The animation of the MD trajectory will allow you to verify if the contents 
of the trajectory are what you expected.
"""


class TrajectoryTab(GeneralTab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core.add_button("Load an .MDT Trajectory", self.load_trajectory)

    @Slot()
    def load_trajectory(self):
        fname = QFileDialog.getOpenFileName(
            self._core,
            "Load an MD trajectory",
            self._session.get_path("root_directory"),
            "MDANSE trajectory files (*.mdt);;HDF5 files (*.h5);;HDF5 files(*.hdf);;All files(*.*)",
        )
        if len(fname[0]) > 0:
            _, short_name = os.path.split(fname[0])
            try:
                data = HDFTrajectoryInputData(fname[0])
            except Exception as e:
                self._core.error(repr(e))
            else:
                self._core._model.append_object(((fname[0], data), short_name))

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="Trajectories",
            session=LocalSession(),
            model=GeneralModel(),
            view=TrajectoryView(),
            visualiser=View3D(),
            layout=partial(TriplePanel, left_panel=TrajectoryInfo()),
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
            view=TrajectoryView(),
            visualiser=View3D(),
            layout=partial(TriplePanel, left_panel=TrajectoryInfo()),
            label_text=label_text,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = TrajectoryTab.standard_instance()
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
