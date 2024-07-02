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
from MDANSE_GUI.Tabs.Layouts.TriplePanel import TriplePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Views.PlotDetailsView import PlotDetailsView
from MDANSE_GUI.Tabs.Visualisers.PlotHolder import PlotHolder
from MDANSE_GUI.Tabs.Visualisers.PlotSettings import PlotSettings
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


label_text = """This tab manages a single plot.
You can change the contents and appearance of the plot
here.
"""


class PlotTab(GeneralTab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._visualiser._settings = self._settings
        self._core._extra_visualiser._settings = self._settings
        self._visualiser.currentChanged.connect(self.switch_model)
        self._view.setModel(self.model)
        self._core._extra_visualiser.plot_settings_changed.connect(
            self._visualiser.update_plots
        )
        self._core._extra_visualiser.plot_settings_changed.connect(
            self.model.regenerate_colours
        )

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="Plotting",
            session=LocalSession(),
            model=PlottingContext(),
            view=PlotDetailsView(),
            visualiser=PlotHolder(),
            layout=partial(TriplePanel, left_panel=PlotSettings()),
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
            model=None,
            view=PlotDetailsView(),
            visualiser=PlotHolder(),
            layout=partial(TriplePanel, left_panel=PlotSettings()),
            label_text=label_text,
        )
        return the_tab

    @property
    def model(self):
        return self._visualiser.model

    @Slot(object)
    def accept_external_data(self, data_model):
        self._visualiser.model.accept_external_data(data_model)
        self._visualiser.plotter.plot_data()

    @Slot(int)
    def switch_model(self, tab_id):
        self._view.setModel(self.model)


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = PlotTab.standard_instance()
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
