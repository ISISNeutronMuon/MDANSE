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

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Views.PlotDetailsView import PlotDetailsView
from MDANSE_GUI.Tabs.Visualisers.PlotHolder import PlotHolder
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


label_text = """This tab manages a single plot.
You can change the contents and appearance of the plot
here.
"""


class PlotTab(GeneralTab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core.add_button("Load .MDA results", self.load_files)

    @Slot()
    def load_files(self):
        fnames = QFileDialog.getOpenFileNames(
            self._core,
            "Load an MDA file (MDANSE analysis results)",
            self._session.get_path("root_directory"),
            "MDANSE result files (*.mda);;HDF5 files (*.h5);;HDF5 files(*.hdf);;All files(*.*)",
        )
        for fname in fnames[0]:
            self.load_results(fname)

    @Slot()
    def load_results(self, fname: str):
        if len(fname) > 0:
            _, short_name = os.path.split(fname)
            self._model.add_file(fname)

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="Plotting",
            session=LocalSession(),
            model=PlottingContext(),
            view=PlotDetailsView(),
            visualiser=PlotHolder(),
            layout=DoublePanel,
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
            model=kwargs.get("model", PlottingContext()),
            view=PlotDetailsView(),
            visualiser=PlotHolder(),
            layout=DoublePanel,
            label_text=label_text,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = PlotTab.standard_instance()
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
