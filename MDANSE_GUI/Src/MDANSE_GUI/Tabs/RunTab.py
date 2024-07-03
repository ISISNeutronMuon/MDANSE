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

from qtpy.QtWidgets import QWidget

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.MultiPanel import MultiPanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Models.JobHolder import JobHolder
from MDANSE_GUI.Tabs.Views.RunTable import RunTable
from MDANSE_GUI.Tabs.Visualisers.JobLogInfo import JobLogInfo


run_tab_label = """This table shows the status of jobs
which have been started in your session.
You can check which jobs were successful,
and if they failed, you can see the details
of the error message.
"""


class RunTab(GeneralTab):
    """The tab for tracking the progress of running jobs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="RunMonitor",
            model=JobHolder(),
            view=RunTable(),
            visualiser=TextInfo(
                header="MDANSE Jobs",
                footer="Look up our Read The Docs page:"
                + "https://mdanse.readthedocs.io/en/protos/",
            ),
            layout=partial(
                MultiPanel, right_panels=[JobLogInfo(header="MDANSE Logs")],
            ),
            label_text=run_tab_label,
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
            model=kwargs.get("model", JobHolder()),
            view=RunTable(),
            visualiser=TextInfo(
                header="MDANSE Jobs",
                footer="Look up our "
                + '<a href="https://mdanse.readthedocs.io/en/protos/">Read The Docs</a>'
                + " page.",
            ),
            layout=partial(
                MultiPanel, right_panels=[JobLogInfo(header="MDANSE Logs")],
            ),
            label_text=run_tab_label,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = RunTab(
        window,
        name="RunningJobs",
        model=JobHolder(),
        view=RunTable(),
        visualiser=TextInfo(),
        layout=partial(MultiPanel, right_panels=[JobLogInfo()]),
        label_text=run_tab_label,
    )
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
