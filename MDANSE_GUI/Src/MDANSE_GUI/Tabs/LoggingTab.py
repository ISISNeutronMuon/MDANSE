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


from qtpy.QtCore import QObject, Slot, Signal, QMessageLogger, qInstallMessageHandler
from qtpy.QtWidgets import QWidget

from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.SinglePanel import SinglePanel
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Tabs.Models.JobHolder import JobHolder
from MDANSE_GUI.Tabs.Views.RunTable import RunTable


log_tab_label = """MDANSE_GUI message log.
"""


class LoggingTab(GeneralTab):
    """The tab for tracking the progress of running jobs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qInstallMessageHandler(self.log_handler)

    def log_handler(self, m_type, m_context, m_text):
        self._visualiser.append_text(m_text)

    @classmethod
    def standard_instance(cls):
        the_tab = cls(
            window,
            name="Logger",
            visualiser=TextInfo(),
            layout=SinglePanel,
            label_text=log_tab_label,
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
            visualiser=TextInfo(),
            layout=SinglePanel,
            label_text=log_tab_label,
        )
        return the_tab


if __name__ == "__main__":
    import sys
    from qtpy.QtWidgets import QApplication, QMainWindow, QVBoxLayout

    app = QApplication(sys.argv)
    window = QMainWindow()
    the_tab = LoggingTab(
        window,
        name="RunningJobs",
        visualiser=TextInfo(),
        layout=SinglePanel,
        label_text=log_tab_label,
    )
    window.setCentralWidget(the_tab._core)
    window.show()
    app.exec()
