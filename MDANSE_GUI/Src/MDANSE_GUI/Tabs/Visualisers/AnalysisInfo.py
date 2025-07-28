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

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QTextBrowser

from MDANSE.Framework.Jobs.IJob import IJob


class AnalysisInfo(QTextBrowser):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        self._header = kwargs.pop("header", "")
        self._footer = kwargs.pop("footer", "")
        super().__init__(*args, **kwargs)
        self.setOpenExternalLinks(True)

    @Slot(object)
    def update_panel(self, incoming: object):
        filtered = self.filter(incoming)
        self.setHtml(filtered)

    def filter(self, some_text: str, line_break="<br />"):
        new_text = ""
        if self._header:
            new_text += self._header + line_break
        if some_text is not None:
            new_text += line_break.join([x.strip() for x in some_text.split("\n")])
        if self._footer:
            new_text += line_break + self._footer
        return new_text

    def summarise_chemical_system(self, job_name):
        try:
            temp_instance = IJob.create(job_name)
        except Exception:
            return ""
        text = "\n ==== Input Parameter summary ==== \n"
        params = temp_instance.get_default_parameters()
        for key, value in params.items():
            try:
                text += f"parameters['{key}'] = {value[0]} # {value[1]} \n"
            except Exception:
                continue
        text += " ===== \n"
        return text
