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
from MDANSE_GUI.Tabs.Layouts.MultiPanel import MultiPanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Models.PlotDataModel import PlotDataModel
from MDANSE_GUI.Tabs.Views.PlotDataView import PlotDataView
from MDANSE_GUI.Tabs.Visualisers.PlotDataInfo import PlotDataInfo
from MDANSE_GUI.Tabs.Visualisers.DataPlotter import DataPlotter


label_text = """Here you can create plots of specific
data sets. Load the files and assign the data sets
to a plot. The plotting interface will appear
in a new tab of the interface.
"""


class PlotSelectionTab(GeneralTab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core.add_button("Load .MDA results", self.load_files)
        self._visualiser._settings = self._settings
        self._visualiser._unit_lookup = self

    def grouped_settings(self):
        results = super().grouped_settings()
        results += [
            [
                "dialogs",
                {"new_plot": "True", "data_plotted": "True"},
                {
                    "new_plot": "Show a pop-up dialog EVERY TIME a new plot is created",
                    "data_plotted": "Show a pop-up dialog EVERY TIME a data set is plotted",
                },
            ]
        ]
        return results

    @Slot()
    def load_files(self):
        fnames = QFileDialog.getOpenFileNames(
            self._core,
            "Load an MDA file (MDANSE analysis results)",
            self.get_path("plot_selection"),
            "MDANSE result files (*.mda);;HDF5 files (*.h5);;HDF5 files(*.hdf);;All files(*.*)",
        )
        if fnames is None:
            return
        if len(fnames[0]) < 1:
            return
        for fname in fnames[0]:
            self.load_results(fname)
            last_path, _ = os.path.split(fname)
        self.set_path("plot_selection", last_path)

    @Slot(str)
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
            model=PlotDataModel(),
            view=PlotDataView(),
            visualiser=DataPlotter(),
            layout=partial(MultiPanel, left_panels=[PlotDataInfo()]),
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
            model=kwargs.get("model", PlotDataModel()),
            view=PlotDataView(),
            visualiser=DataPlotter(),
            layout=partial(MultiPanel, left_panels=[PlotDataInfo()]),
            label_text=label_text,
        )
        the_tab._visualiser._unit_lookup = the_tab
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = PlotSelectionTab.standard_instance()
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
