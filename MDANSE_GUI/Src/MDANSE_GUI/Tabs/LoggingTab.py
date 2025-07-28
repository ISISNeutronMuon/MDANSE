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

from logging import Handler, LogRecord

from qtpy.QtCore import Slot, qInstallMessageHandler
from qtpy.QtWidgets import QComboBox, QWidget

from MDANSE.MLogging import FMT, LOG
from MDANSE_GUI.Session.LocalSession import LocalSession
from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.SinglePanel import SinglePanel
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Widgets.DefaultCombobox import highlight_default_value

log_tab_label = """MDANSE_GUI <b>message log.</b>
<br><br>
This tab will display the general logging messages of the graphical interface.
You can adjust the logging level using the combo box below.
"""


class GuiLogHandler(Handler):
    def __init__(self, *args, **kwargs):
        self._visualiser = None
        super().__init__(*args, **kwargs)
        self.setFormatter(FMT)

    def add_visualiser(self, new_visualiser):
        self._visualiser = new_visualiser

    def emit(self, record: LogRecord):
        if self._visualiser is not None:
            message = self.formatter.format(record)
            if "WARNING" in message:
                message = f'<span style="color:orange;">{message}</span>'
            elif "ERROR" in message or "CRITICAL" in message:
                message = f'<span style="color:red;">{message}</span>'
            else:
                message = f"<span>{message}</span>"
            self._visualiser.append_text(message)


class LoggingTab(GeneralTab):
    """The tab for tracking the progress of running jobs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._extra_handler = None
        self._visualiser.toHtml()
        qInstallMessageHandler(self.log_qt_handler)
        self._loglevel_combo = QComboBox(self._core)
        self._loglevel_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
        self._loglevel_combo.setCurrentText("INFO")
        self._loglevel_combo.currentTextChanged.connect(self.change_log_level)
        highlight_default_value(self._loglevel_combo)
        self._core._ub_layout.addWidget(self._loglevel_combo)

    @Slot(str)
    def change_log_level(self, new_level: str):
        if self._extra_handler is None:
            return
        try:
            self._extra_handler.setLevel(new_level)
        except Exception:
            LOG.error(f"Could not set GuiLogHandler to log level {new_level}")
        else:
            self._visualiser.append_text(
                f"<b>=== Log level changed to {new_level} ===</b>"
            )

    def add_handler(self, new_handler):
        try:
            current_level = self._loglevel_combo.currentText()
        except Exception:
            current_level = "INFO"
        self._extra_handler = new_handler
        self._extra_handler.add_visualiser(self._visualiser)
        self.change_log_level(current_level)

    def log_qt_handler(self, m_type, m_context, m_text):
        self._visualiser.append_text(f"Qt log message (type={m_type})=" + m_text)

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
