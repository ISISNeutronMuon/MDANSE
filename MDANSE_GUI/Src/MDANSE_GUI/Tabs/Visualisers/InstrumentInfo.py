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

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtGui import QStandardItem
from qtpy.QtWidgets import QTextBrowser

from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE_GUI.Widgets.ResolutionWidget import ResolutionCalculator, widget_text_map


class SimpleInstrument:
    sample_options = ["isotropic", "crystal"]
    technique_options = ["QENS", "INS"]
    resolution_options = [str(x) for x in widget_text_map.keys()]
    qvector_options = [str(x) for x in IQVectors.indirect_subclasses()]
    energy_units = ["meV", "1/cm", "THz"]
    momentum_units = ["1/ang", "1/nm", "1/Bohr"]

    def __init__(self, optional_qitem_reference: QStandardItem = None) -> None:
        self._list_item = optional_qitem_reference
        self._name = "Generic neutron instrument"
        self._name_is_fixed = False
        self._sample = "isotropic"
        self._technique = "QENS"
        self._resolution_type = "Gaussian"
        self._resolution_fwhm = 0.1
        self._resolution_unit = "meV"
        self._qvector_type = "SphericalQVectors"
        self._q_min = 0.1
        self._q_max = 10.0
        self._q_unit = "1/ang"
        self._q_step = 1.0
        self._q_width = 1.0
        self._axis_1 = [1, 0, 0]
        self._axis_2 = [0, 1, 0]
        self._vectors_per_shell = 100
        self._configured = False
        self._model_index = -1

    @classmethod
    def inputs(cls):
        input_list = [
            ["_name", "QLineEdit", "str"],
            ["_sample", "QComboBox", "sample_options"],
            ["_technique", "QComboBox", "technique_options"],
            ["_resolution_type", "QComboBox", "resolution_options"],
            ["_resolution_fwhm", "QLineEdit", "float"],
            ["_resolution_unit", "QComboBox", "energy_units"],
            ["_qvector_type", "QComboBox", "qvector_options"],
            ["_q_unit", "QComboBox", "momentum_units"],
            ["_q_min", "QLineEdit", "float"],
            ["_q_max", "QLineEdit", "float"],
            ["_q_step", "QLineEdit", "float"],
            ["_q_width", "QLineEdit", "float"],
            ["_vectors_per_shell", "QLineEdit", "int"],
            ["_axis_1", "VectorWidget", "float"],
            ["_axis_2", "VectorWidget", "float"],
        ]
        return input_list

    def update_item(self):
        if self._list_item is None:
            return
        self._list_item.setData(self._name, role=Qt.ItemDataRole.DisplayRole)
        self._list_item.setText(self._name)

    def create_resolution_params(self):
        if not self._configured:
            return
        calculator = ResolutionCalculator()
        try:
            calculator.update_model(self._resolution_type)
        except Exception as e:
            LOG.error(f"update_model failed: {e}")
        try:
            calculator.recalculate_peak(
                self._resolution_fwhm, 0.0, 0.0, self._resolution_unit
            )
        except Exception as e:
            LOG.error(f"recalculate_peak failed: {e}")
        _, results = calculator.summarise_results()
        results.pop("function", None)
        mdanse_tuple = (widget_text_map[self._resolution_type], results)
        self._resolution_results = mdanse_tuple
        return mdanse_tuple

    def sanitize_numbers(self):
        results = []
        for entry in [self._q_step, self._q_min, self._q_max, self._q_width]:
            try:
                new_entry = float(entry)
            except ValueError:
                if "e" in entry:
                    try:
                        new_entry = float(entry.split("e")[0])
                    except ValueError:
                        new_entry = 1.0
            results.append(new_entry)
        return results

    def create_q_vector_params(self, sample_configuration=None):
        if not self._configured:
            return
        cov_type = self._qvector_type
        try:
            qvec_generator = IQVectors.create(cov_type, sample_configuration)
        except ValueError:
            return ("No qvectors", {})
        except AttributeError:
            return (cov_type, {})
        qvec_generator.build_configuration()
        param_dictionary = {}
        _q_step, _q_min, _q_max, _q_width = self.sanitize_numbers()
        try:
            conversion_factor = measure(1.0, iunit=self._q_unit).toval("1/nm")
        except Exception:
            raise ValueError(f"Could not convert unit: {self._q_unit}")
        else:
            conversion_factor = float(conversion_factor)
        if "shells" in qvec_generator._configuration:
            q_step = round(conversion_factor * float(_q_step), 6)
            q_min = round(conversion_factor * float(_q_min), 6)
            q_max = round(conversion_factor * float(_q_max), 6)
            param_dictionary["shells"] = [q_min, q_max, q_step]
        if "width" in qvec_generator._configuration:
            width = round(conversion_factor * float(_q_width), 6)
            param_dictionary["width"] = width
        if "n_vectors" in qvec_generator._configuration:
            num_vectors = int(self._vectors_per_shell)
            param_dictionary["n_vectors"] = num_vectors
        if "axis" in qvec_generator._configuration:
            ax_vector = [float(x) for x in self._axis_1.split(",")]
            param_dictionary["axis"] = ax_vector
        if "axis_1" in qvec_generator._configuration:
            ax_vector = [float(x) for x in self._axis_1.split(",")]
            param_dictionary["axis_1"] = ax_vector
        if "axis_2" in qvec_generator._configuration:
            ax_vector = [float(x) for x in self._axis_2.split(",")]
            param_dictionary["axis_2"] = ax_vector
        mdanse_tuple = (
            cov_type,
            param_dictionary,
        )
        return mdanse_tuple

    def filter_qvector_generator(self):
        new_list = [str(x) for x in self.qvector_options]
        if self._sample == "isotropic":
            new_list = [str(x) for x in new_list if "Dispersion" not in x]
        if self._technique == "QENS":
            new_list = [str(x) for x in new_list if "Spherical" in x]
        return new_list

    def pick_qvector_generator(self) -> str:
        qgenerator = "SphericalQVectors"
        if self._sample == "isotropic" and self._technique == "QENS":
            qgenerator = "SphericalLatticeQVectors"
        return qgenerator


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
        try:
            filtered = self.filter(incoming)
        except Exception as e:
            LOG.error(f"Error in InstrumentInfo: {e}")
            self.setHtml("")
        else:
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
        new_text += "<b>" + instrument_object._name + "</b>" + line_break + line_break
        new_text += "MDANSE resolution input" + line_break
        new_text += str(instrument_object.create_resolution_params()) + line_break
        new_text += "MDANSE q-vector generator input" + line_break
        new_text += str(instrument_object.create_q_vector_params()) + line_break
        if self._footer:
            new_text += line_break + self._footer
        return new_text
