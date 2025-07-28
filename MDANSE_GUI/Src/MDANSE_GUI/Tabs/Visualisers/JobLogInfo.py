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

from collections.abc import Iterable
from typing import Literal

from qtpy.QtCore import Slot

from .TextInfo import TextInfo

ErrorTypes = Literal["WARNING", "ERROR", "CRITICAL", "DEBUG", "INFO"]


class JobLogInfo(TextInfo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("font-family: Courier New;")

    @Slot(object)
    def update_panel(self, incoming: tuple[Iterable[str], Iterable[ErrorTypes]]):
        msgs, levels = incoming
        text = ""

        for msg, level in zip(msgs, levels):
            if level == "WARNING":
                text += f'<span style="color:orange;">{msg}</span>\n'
            elif level in {"ERROR", "CRITICAL"}:
                text += f'<span style="color:red;">{msg}</span>\n'
            else:
                text += f"<span>{msg}</span>\n"

        filtered = self.filter(text)
        self.setHtml(filtered)
