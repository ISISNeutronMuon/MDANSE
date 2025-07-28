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

from functools import partial

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QDialog, QWidget

from MDANSE.MLogging import LOG
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.MultiPanel import MultiPanel
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext
from MDANSE_GUI.Tabs.Views.PlotDetailsView import PlotDetailsView
from MDANSE_GUI.Tabs.Visualisers.PlotHolder import PlotHolder
from MDANSE_GUI.Tabs.Visualisers.PlotSettings import PlotSettings
from MDANSE_GUI.Widgets.PlotSettingsDialog import PlotSettingsEditor

label_text = """<b>View and customise the existing plots.</b>
<br><br>
You can change the contents and appearance of the plot
here.
<br><br>
The button below allows you to edit most of the configuration parameters
of the plotting library. Please keep in mind that the parameters which
affect some basic properties of a figure (such as the dimensions or the
DPI value) will not affect the existing plots and will only have an effect
on the plots created after the change.
"""


class PlotTab(GeneralTab):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._visualiser._unit_lookup = self
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
        self._core._extra_visualiser.make_layout()
        self.matplotlib_dialog = PlotSettingsEditor(settings=self._settings)
        self.matplotlib_dialog.values_changed.connect(self._visualiser.update_plots)
        self._core.add_button("Change matplotlib settings", self.edit_matplotlib)

    def launch_dialog(self, dialog: QDialog) -> None:
        if dialog.isVisible():
            geometry = dialog.saveGeometry()
            dialog.previous_geometry = geometry
            dialog.close()
        else:
            if hasattr(dialog, "previous_geometry"):
                dialog.restoreGeometry(dialog.previous_geometry)
            dialog.show()

    def edit_matplotlib(self):
        self.launch_dialog(self.matplotlib_dialog)

    @classmethod
    def standard_instance(cls):
        plt_settings = PlotSettings()
        the_tab = cls(
            window,
            name="Plotting",
            session=LocalSession(),
            model=PlottingContext(),
            view=PlotDetailsView(),
            visualiser=PlotHolder(),
            layout=partial(
                MultiPanel, left_panels=[plt_settings], extra_visualiser=plt_settings
            ),
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
        plt_settings = PlotSettings(settings=settings)
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=None,
            view=PlotDetailsView(),
            visualiser=PlotHolder(),
            layout=partial(
                MultiPanel, left_panels=[plt_settings], extra_visualiser=plt_settings
            ),
            label_text=label_text,
        )
        the_tab._visualiser._unit_lookup = the_tab
        the_tab._visualiser.new_entry.connect(the_tab.tab_notification)
        return the_tab

    @property
    def model(self):
        return self._visualiser.model

    @Slot(object)
    def accept_external_data(self, data_model):
        LOG.debug(f"accept_external_data received {data_model}")
        try:
            self._visualiser.model.accept_external_data(data_model)
        except Exception as e:
            LOG.error(f"Visualiser failed to pass data model: {e}")
        else:
            try:
                self._visualiser.plotter.plot_data()
            except Exception as e2:
                LOG.error(f"Visualiser failed to plot data: {e2}")
            else:
                self.tab_notification()

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
