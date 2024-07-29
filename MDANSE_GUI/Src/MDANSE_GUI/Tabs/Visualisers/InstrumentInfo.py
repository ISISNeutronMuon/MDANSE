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
from qtpy.QtCore import Slot, Signal
from qtpy.QtWidgets import QTextBrowser

from MDANSE_GUI.Tabs.Visualisers.InstrumentDetails import SimpleInstrument


class InstrumentInfo(QTextBrowser):
    error = Signal(str)

    def __init__(self, *args, **kwargs):
        self._header = kwargs.pop("header", "")
        self._footer = kwargs.pop("footer", "")
        super().__init__(*args, **kwargs)
        self.setOpenExternalLinks(True)
        self.setHtml("")

    @Slot(object)
    def update_panel(self, incoming: SimpleInstrument):
        filtered = self.filter(incoming)
        self.setHtml(filtered)

    @Slot(str)
    def append_text(self, new_text: str):
        self.append(new_text)

    def filter(self, instrument_object: SimpleInstrument, line_break="<br />") -> str:
        """Extracts and displays results calculated by SimpleInstrument.

        Parameters
        ----------
        instrument_object : SimpleInstrument
            Class containing a neutron instrument definition
        line_break : str, optional
            Text formatting option, by default "<br />" (HTML line break)

        Returns
        -------
        str
            Formatted text
        """

        new_text = ""
        if self._header:
            new_text += self._header + line_break
        new_text += instrument_object._name + line_break
        new_text += "MDANSE resolution input" + line_break
        new_text += instrument_object.create_resolution_params() + line_break
        new_text += "MDANSE q-vector generator input" + line_break
        new_text += instrument_object.create_q_vector_params() + line_break
        if self._footer:
            new_text += line_break + self._footer
        return new_text
