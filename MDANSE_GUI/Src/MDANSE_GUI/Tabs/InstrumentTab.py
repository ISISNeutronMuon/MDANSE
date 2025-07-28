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

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget

from MDANSE import PLATFORM
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Views.InstrumentList import InstrumentList
from MDANSE_GUI.Tabs.Visualisers.InstrumentDetails import InstrumentDetails

label_text = """Here you can browse, edit and add <b>instrument profiles.</b>
<br><br>
If you are trying to reproduce the results of a neutron experiment,
you will need to set at least the correct instrument resolution
and q-vector coverage to be used in the analysis.
<br><br>
The initial inputs of an analysis in the GUI will be affected
by the instrument profile you chose. You can still change them
before starting the analysis, if you had something else in mind.
"""


class InstrumentTab(GeneralTab):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core.add_button("Create Instrument", self._view.add_instrument)
        self._core.add_button("Save Instruments", self._view.save_to_file, upper=False)
        self._view.introduce_empty_instrument()
        current_path = os.path.dirname(os.path.abspath(__file__))
        builtin_file = os.path.join(
            current_path, "..", "Resources", "InstrumentDefinitions.toml"
        )
        try:
            self._view.load_from_file(builtin_file, keep_backups=True)
        except Exception as e:
            LOG.error(f"Could not load instruments from {builtin_file}: {e}")
        filename = os.path.join(
            PLATFORM.application_directory(), "InstrumentDefinitions.toml"
        )
        try:
            self._view.load_from_file(filename)
        except Exception as e:
            LOG.error(f"Could not load instruments from {filename}: {e}")
        for instrument in self._model._nodes.values():
            if instrument is not None:
                instrument.update_item()
                instrument._configured = (
                    True  # instruments loaded from file are configured
                )

    @Slot()
    def load_trajectories(self):
        self._view.add_instrument()

    @Slot(str)
    def load_trajectory(self, some_fname: str):
        fname = str(some_fname)
        if len(fname) > 0:
            _, short_name = os.path.split(fname)
            try:
                data = Trajectory(fname)
            except Exception as e:
                self._core.error.emit(repr(e))
            else:
                self._core._model.append_object(((fname, data), short_name))

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="Instruments",
            session=LocalSession(),
            model=GeneralModel(),
            view=InstrumentList(),
            visualiser=InstrumentDetails(),
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
            model=kwargs.get("model", GeneralModel()),
            view=InstrumentList(),
            visualiser=InstrumentDetails(),
            layout=DoublePanel,
            label_text=label_text,
        )
        return the_tab


if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = InstrumentTab.standard_instance()
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
