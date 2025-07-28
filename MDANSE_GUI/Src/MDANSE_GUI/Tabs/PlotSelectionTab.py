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
from qtpy.QtWidgets import QFileDialog, QWidget

from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.MultiPanel import MultiPanel
from MDANSE_GUI.Tabs.Models.PlotDataModel import PlotDataModel
from MDANSE_GUI.Tabs.Views.PlotDataView import PlotDataView
from MDANSE_GUI.Tabs.Visualisers.DataPlotter import DataPlotter
from MDANSE_GUI.Tabs.Visualisers.PlotDataInfo import PlotDataInfo

label_text = """Load files and <b>assign data sets
to a plot.</b>
<br><br>
The plots created or updated using the buttons below
will <b>appear in the next tab.</b>
<br><br>
<b>Fast plotting</b> into a new plot is done by <b>double-clicking</b> an item:
<ul>
<li>double click a file to plot the main results from that file,</li>
<li>double click a dataset to plot it,</li>
<li>double click a group to plot only the datasets directly in the group (skipping the nested ones),</li>
</ul>
"""


class PlotSelectionTab(GeneralTab):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core.add_button("Load .MDA results", self.load_files)
        self._visualiser._settings = self._settings
        self._visualiser._unit_lookup = self

    def grouped_settings(self):
        return super().grouped_settings() | {
            "dialogs": (
                {"new_plot": "True", "data_plotted": "True", "new_text": "True"},
                {
                    "new_plot": "Show a pop-up dialog EVERY TIME a new plot is created",
                    "data_plotted": "Show a pop-up dialog EVERY TIME a data set is plotted",
                    "new_text": "Show a pop-up dialog EVERY TIME a new data view is created",
                },
            )
        }

    @Slot()
    def load_files(self):
        fnames = QFileDialog.getOpenFileNames(
            self._core,
            "Load an MDA file (MDANSE analysis results)",
            str(self.get_path("plot_selection")),
            "MDANSE result files (*.mda);;HDF5 files (*.h5);;HDF5 files(*.hdf);;All files(*.*)",
        )
        if fnames is None:
            return
        if len(fnames[0]) < 1:
            return
        for fname in fnames[0]:
            self.load_results(str(PurePath(fname)))
            last_path = str(PurePath(os.path.split(fname)[0]))
        self.set_path("plot_selection", last_path)

    @Slot(str)
    def load_results(self, some_fname: str):
        fname = PurePath(some_fname)
        if len(str(fname)) > 0:
            fname = os.path.abspath(fname)
            self._model.add_file(str(fname))
            self._session.protect_filename(fname)

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
        the_tab._view.free_name.connect(session.free_filename)
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
