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
from collections import defaultdict

from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QTextBrowser


class TrajectoryInfo(QTextBrowser):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        self._header = kwargs.pop("header", "")
        self._footer = kwargs.pop("footer", "")
        super().__init__(*args, **kwargs)
        self.setOpenExternalLinks(True)

    @Slot(object)
    def update_panel(self, data: tuple):
        fullpath, incoming = data
        try:
            text = incoming.info()  # this is from a trajectory object
        except AttributeError:
            self.error.emit(f"Trajectory info received {incoming}")
            self.clear()
            return
        try:
            cs = incoming.chemical_system
        except AttributeError:
            self.error.emit(f"Trajectory {incoming} has no chemical system")
        else:
            text += self.summarise_chemical_system(cs)
        filtered = self.filter(text)
        self.setHtml(filtered)

    def summarise_chemical_system(self, cs):
        text = "\n ==== Chemical System summary ==== \n"
        counter = defaultdict(int)
        for atom in cs.atom_list:
            counter[(atom.full_name, atom.symbol)] += 1
        for key, value in counter.items():
            text += f"Full Name: {key[0]}; Element: {key[1]}; Count: {value}\n"
        text += " ===== \n"
        return text

    def filter(self, some_text: str, line_break="<br />"):
        new_text = ""
        if self._header:
            new_text += self._header + line_break
        if some_text is not None:
            new_text += line_break.join([x.strip() for x in some_text.split("\n")])
        if self._footer:
            new_text += line_break + self._footer
        return new_text
