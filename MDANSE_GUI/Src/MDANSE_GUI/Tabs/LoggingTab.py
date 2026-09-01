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

import html
import logging
from logging import Handler, LogRecord
from typing import TYPE_CHECKING, ClassVar

from qtpy.QtCore import Signal, Slot, qInstallMessageHandler
from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget
from typing_extensions import Self

from MDANSE.MLogging import FMT, LOG
from MDANSE_GUI.Tabs.GeneralTab import GeneralTab
from MDANSE_GUI.Tabs.Layouts.SinglePanel import SinglePanel
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Widgets.DefaultCombobox import highlight_default_value

if TYPE_CHECKING:
    from MDANSE_GUI.Session.Session import Session

log_tab_label = """MDANSE_GUI <b>message log.</b>
<br><br>
This tab will display the general logging messages of the graphical interface.
You can adjust the logging level using the combo box below.
"""


class GuiLogHandler(Handler):
    """Log handler to send message to GUI logger."""

    new_log = Signal(int)

    def __init__(self, *args, **kwargs) -> None:
        self._visualiser: LogInfo | None = None
        super().__init__(*args, **kwargs)
        self.setFormatter(FMT)

    def add_visualiser(self, new_visualiser: LogInfo | None) -> None:
        self._visualiser = new_visualiser

    def emit(self, record: LogRecord) -> None:
        if self._visualiser is not None:
            self._visualiser.append_log(self.formatter.format(record), record)


class LogInfo(TextInfo):
    """Extended TextInfo for handling error logs."""

    new_log = Signal(object)

    colours: ClassVar[dict[int, str | None]] = {
        logging.WARNING: "orange",
        logging.ERROR: "red",
        logging.CRITICAL: "red",
    }
    MESSAGE_FMT: ClassVar[str] = '<span style="color:{colour};">{message}</span>'

    def append_log(self, message: str, record: LogRecord) -> None:
        if (colour := self.colours.get(record.levelno)) is not None:
            message = self.MESSAGE_FMT.format(colour=colour, message=message)

        self.append_text(message)
        self.new_log.emit(record)


class LoggingTab(GeneralTab):
    """The tab for tracking the progress of running jobs."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        assert isinstance(self._visualiser, LogInfo)

        self._extra_handler = None
        self._visualiser.toHtml()
        self._visualiser.new_log.connect(self.handle_new_log)
        qInstallMessageHandler(self.log_qt_handler)

        bbox = QHBoxLayout()

        log_label = QLabel("Report level")
        self._loglevel_combo = QComboBox()
        self._loglevel_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])
        self._loglevel_combo.setCurrentText("INFO")
        self._loglevel_combo.currentTextChanged.connect(self.change_log_level)
        highlight_default_value(self._loglevel_combo)

        alert_label = QLabel("Alert level")
        self._alertlevel_combo = QComboBox()
        self._alertlevel_combo.addItems(
            ["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]
        )
        self._alertlevel_combo.setCurrentText("ERROR")
        self._alertlevel_combo.currentTextChanged.connect(self.change_alert_level)
        self._alert_level = logging.ERROR
        highlight_default_value(self._alertlevel_combo)

        bbox.addWidget(log_label)
        bbox.addWidget(self._loglevel_combo)
        bbox.addWidget(alert_label)
        bbox.addWidget(self._alertlevel_combo)

        self._core._ub_layout.addLayout(bbox)

    @Slot(str)
    def change_log_level(self, new_level: str) -> None:
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

    @Slot(str)
    def change_alert_level(self, new_level: str) -> None:
        try:
            self._alert_level = getattr(logging, new_level, logging.ERROR)
        except Exception:
            LOG.error(f"Could not set alert to log level {new_level}")
        else:
            self._visualiser.append_text(
                f"<b>=== Alert level changed to {new_level} ===</b>"
            )

    def add_handler(self, new_handler: GuiLogHandler) -> None:
        """Add log handler."""
        try:
            current_level = self._loglevel_combo.currentText()
        except Exception:
            current_level = "INFO"
        self._extra_handler = new_handler
        self._extra_handler.add_visualiser(self._visualiser)
        self.change_log_level(current_level)

    @Slot(object)
    def handle_new_log(self, record: LogRecord) -> None:
        if record.levelno >= self._alert_level:
            self.tab_notification()

    def log_qt_handler(self, m_type, m_context, m_text):
        self._visualiser.append_text(f"Qt log message (type={m_type})=" + m_text)

    @classmethod
    def gui_instance(
        cls,
        parent: QWidget,
        name: str,
        session: Session,
        settings,
        logger,
        **kwargs,
    ) -> Self:
        the_tab = cls(
            parent,
            name=name,
            session=session,
            settings=settings,
            logger=logger,
            visualiser=LogInfo(footer="", font="Courier New"),
            layout=SinglePanel,
            label_text=log_tab_label,
        )
        return the_tab
