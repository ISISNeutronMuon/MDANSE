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

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Views.TrajectoryView import TrajectoryView
from MDANSE_GUI.Tabs.Visualisers.TrajectoryInfo import TrajectoryInfo


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
                self._core._model.append_object((fname[0], short_name))

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="Trajectories",
            session=LocalSession(),
            model=GeneralModel(),
            view=TrajectoryView(),
            visualiser=TrajectoryInfo(),
            layout=DoublePanel,
            label_text="""Here you can load the .mdt files.
They are MD trajectories in HDF5 format,
created by one of the MDANSE converters.
""",
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
            visualiser=TrajectoryInfo(),
            layout=DoublePanel,
            label_text="""Here you can load the .mdt files.
They are MD trajectories in HDF5 format,
created by one of the MDANSE converters.
""",
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = TrajectoryTab.standard_instance()
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
