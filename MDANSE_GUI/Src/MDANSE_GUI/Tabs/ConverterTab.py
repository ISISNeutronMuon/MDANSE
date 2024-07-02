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
from functools import partial
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QWidget

from MDANSE.Framework.Converters.Converter import Converter

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.TriplePanel import TriplePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Visualisers.Action import Action
from MDANSE_GUI.Tabs.Models.JobTree import JobTree
from MDANSE_GUI.Tabs.Views.ActionsTree import ActionsTree


tab_label = """Convert your trajectory to the MDANSE MDT format.
If you cannot find a dedciated converter
for your MD engine, the ASE converter
can be tried as a backup option.
"""


class ConverterTab(GeneralTab):
    """The tab for choosing and starting a new job."""

    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop("action")
        super().__init__(*args, **kwargs)
        self._current_trajectory = ""
        self._job_starter = None

    def set_job_starter(self, job_starter):
        self._job_starter = job_starter
        self.action.new_thread_objects.connect(self._job_starter.startProcess)

    @Slot(str)
    def set_current_trajectory(self, new_name: str):
        self._current_trajectory = new_name

    @classmethod
    def standard_instance(cls):
        action = Action()
        the_tab = cls(
            window,
            name="AvailableJobs",
            model=JobTree(parent_class=Converter),
            view=ActionsTree(),
            visualiser=action,
            layout=partial(
                TriplePanel,
                left_panel=TextInfo(
                    header="MDANSE Converter",
                    footer="Look up our Read The Docs page:"
                    + "https://mdanse.readthedocs.io/en/protos/",
                ),
            ),
            label_text=tab_label,
            action=action,
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
        action = Action()
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            model=kwargs.get("model", JobTree(parent_class=Converter)),
            view=ActionsTree(),
            visualiser=action,
            layout=partial(
                TriplePanel,
                left_panel=TextInfo(
                    header="MDANSE Converter",
                    footer="Look up our "
                    + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                    + " page.",
                ),
            ),
            label_text=tab_label,
            action=action,
        )
        action.set_settings(the_tab._settings)
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    window = QMainWindow()
    action = Action()
    the_tab = ConverterTab(
        window,
        name="AvailableJobs",
        model=JobTree(parent_class=Converter),
        view=ActionsTree(),
        visualiser=action,
        layout=partial(
            TriplePanel,
            left_panel=TextInfo(
                header="MDANSE Converters",
                footer="Look up our "
                + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                + " page.",
            ),
        ),
        label_text=tab_label,
        action=action,
    )
    the_tab._current_trajectory = "/Users/maciej.bartkowiak/an_example/BLAH.mdt"
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
