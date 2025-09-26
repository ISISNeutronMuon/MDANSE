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
from .MathRenderer import MathRenderer


class TextInfo(QTextBrowser):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        self._header = kwargs.pop("header", "")
        self._footer = kwargs.pop("footer", "")
        super().__init__(*args, **kwargs)
        self.setOpenExternalLinks(True)
        self.setHtml(self.filter(""))

    @Slot(object)
    def update_panel(self, incoming: object):
        filtered = self.filter(incoming)
        self.setHtml(filtered)

    @Slot(str)
    def append_text(self, new_text: str):
        self.append(new_text)

    def filter(self, some_text: str, line_break="<br />"):
        new_text = ""
        if self._header:
            new_text += self._header + line_break
        if some_text is not None:
            new_text += line_break.join([x.strip() for x in some_text.split("\n")])
        if self._footer:
            new_text += line_break + self._footer
        return new_text


class MathInfo(TextInfo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def scan(text: str) -> dict[str, bool]:
        # Instantiate renderer object
        renderer = MathRenderer(text)

        # Scan text for existence of raw LaTex expressions
        scanned = renderer.scan()

        # Iterate over scanned text, rendering LaTex substrings if image not already cached
        for token, is_expression in scanned.items():
            if is_expression:
                if not MathRenderer.cached(token):
                    renderer.render(token)

        return scanned

    def filter(self, some_text: str, line_break="<br />"):
        filtered = super().filter(some_text, line_break)
        scanned = self.scan(filtered)

        html_substrings = []
        for token, is_expression in scanned.items():
            if is_expression:
                image = MathRenderer.from_cache(token)
                html_substrings.append(
                    f'<div style="text-align:center; margin:4px 0;">'
                    f'<img src="data:image/png;base64, {image}"></div>'
                )
            else:
                html_substrings.append(f"<p>{token}</p>")

        return "".join(html_substrings)
