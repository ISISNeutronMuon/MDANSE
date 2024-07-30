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
from qtpy.QtCore import Signal, Slot, Qt
from qtpy.QtGui import QStandardItem


from MDANSE_GUI.Widgets.ResolutionWidget import ResolutionCalculator, widget_text_map


class SimpleInstrument:

    sample_options = ["isotropic", "crystal"]
    technique_options = ["QENS", "INS"]
    resolution_options = [str(x) for x in widget_text_map.keys()]
    energy_units = ["meV", "1/cm", "THz"]
    momentum_units = ["1/ang", "1/nm", "1/Bohr"]

    def __init__(self, optional_qitem_reference: QStandardItem = None) -> None:
        self._list_item = optional_qitem_reference
        self._name = "Generic neutron instrument"
        self._sample = "isotropic"
        self._technique = "QENS"
        self._resolution_type = "Gaussian"
        self._resolution_fwhm = 0.1
        self._resolution_unit = "meV"
        self._q_min = 0.1
        self._q_max = 10.0
        self._q_unit = "1/ang"

    @classmethod
    def inputs(cls):
        input_list = [
            ["_name", "QLineEdit", "str"],
            ["_sample", "QComboBox", "sample_options"],
            ["_technique", "QComboBox", "technique_options"],
            ["_resolution_type", "QComboBox", "resolution_options"],
            ["_resolution_fwhm", "QLineEdit", "float"],
            ["_resolution_unit", "QComboBox", "energy_units"],
            ["_q_min", "QLineEdit", "float"],
            ["_q_max", "QLineEdit", "float"],
            ["_q_unit", "QComboBox", "momentum_units"],
        ]
        return input_list

    def update_item(self):
        if self._list_item is None:
            return
        self._list_item.setData(self._name, role=Qt.ItemDataRole.DisplayRole)

    def create_resolution_params(self):
        calculator = ResolutionCalculator()
        try:
            calculator.update_model(self._resolution_type)
        except Exception as e:
            print(f"update_model failed: {e}")
        try:
            calculator.recalculate_peak(
                self._resolution_fwhm, 0.0, 0.0, self._resolution_unit
            )
        except Exception as e:
            print(f"recalculate_peak failed: {e}")
        text, results = calculator.summarise_results()
        self._resolution_results = results
        return text

    def create_q_vector_params(self):
        return ""


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
        if incoming is None:
            return
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
