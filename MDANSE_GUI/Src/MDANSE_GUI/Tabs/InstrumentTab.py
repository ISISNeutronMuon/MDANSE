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
from qtpy.QtWidgets import QWidget

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.DoublePanel import DoublePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel
from MDANSE_GUI.Tabs.Views.InstrumentList import InstrumentList
from MDANSE_GUI.Tabs.Visualisers.InstrumentDetails import InstrumentDetails


label_text = """Here you can browse, edit and add instrument profiles.
If you are trying to reproduce the results of a neutron experiment,
you will need to set at least the correct instrument resolution
and q-vector coverage to be used in the analysis.
The initial inputs of an analysis in the GUI will be affected
by the instrument profile you chose. You can still change them
before starting the analysis, if you had something else in mind.
"""


class InstrumentTab(GeneralTab):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._core.add_button("Create Instrument", self._view.add_instrument)

    @Slot()
    def load_trajectories(self):
        self._view.add_instrument()

    @Slot(str)
    def load_trajectory(self, fname: str):
        if len(fname) > 0:
            _, short_name = os.path.split(fname)
            try:
                data = HDFTrajectoryInputData(fname)
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
