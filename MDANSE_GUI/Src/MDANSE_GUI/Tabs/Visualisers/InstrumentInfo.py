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

from itertools import count
from typing import TYPE_CHECKING, Any

from more_itertools import first_true
from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import QTextBrowser
from typing_extensions import TypedDict

from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG
from MDANSE_GUI.Widgets.ResolutionWidget import (
    WIDGET_TEXT_MAP,
    ResolutionCalculator,
)

if TYPE_CHECKING:
    from qtpy.QtGui import QStandardItem

    from MDANSE.MolecularDynamics.Trajectory import Trajectory


class QVecParamDict(TypedDict, total=False):
    shells: tuple[float, float, float]
    width: float
    n_samples: int
    n_vectors: int
    axis: list[float]
    axis_1: list[float]
    axis_2: list[float]
    force_equal_weights: bool


def generate_name(
    existing_names: set[str] | None,
    prefix: str = "Generic neutron instrument ",
    suffix: str = "",
) -> str:
    """Create a text string different to those in the input set, if provided.

    This function adds numbers to the text string which is the root of the new name.

    Parameters
    ----------
    existing_names : set[str] | None
        Set of all the names that are already in use.
    prefix : str, optional
        Part of the name before the number, by default "Generic neutron instrument".
    suffix : str, optional
        Part of the name after the number, by default "".

    Returns
    -------
    str
        Name composed of prefix, number, suffix using the lowest positive number possible.
    """
    if existing_names is None:
        return f"{prefix}{suffix}"
    name_generator = (f"{prefix}{number}{suffix}" for number in count(1))
    return first_true(name_generator, pred=lambda x: x not in existing_names)


class SimpleInstrument:
    sample_options = ("isotropic", "crystal")
    technique_options = ("QENS", "INS")
    resolution_options = tuple(map(str, WIDGET_TEXT_MAP))
    qvector_options = tuple(map(str, IQVectors.indirect_subclasses()))
    energy_units = ("meV", "1/cm", "THz")
    momentum_units = ("1/ang", "1/nm", "1/Bohr")

    def __init__(
        self,
        optional_qitem_reference: QStandardItem | None = None,
        existing_names: set[str] | None = None,
    ) -> None:
        self._list_item = optional_qitem_reference
        self._name = generate_name(existing_names)
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
        self._number_of_samples = 100000
        self._vectors_per_shell = 100
        self._force_equal_weights = False
        self._configured = False
        self._model_index = -1

    @classmethod
    def inputs(cls):
        input_list = [
            ("_name", "QLineEdit", "str"),
            ("_sample", "QComboBox", "sample_options"),
            ("_technique", "QComboBox", "technique_options"),
            ("_resolution_type", "QComboBox", "resolution_options"),
            ("_resolution_fwhm", "QLineEdit", "float"),
            ("_resolution_unit", "QComboBox", "energy_units"),
            ("_qvector_type", "QComboBox", "qvector_options"),
            ("_q_unit", "QComboBox", "momentum_units"),
            ("_q_min", "QLineEdit", "float"),
            ("_q_max", "QLineEdit", "float"),
            ("_q_step", "QLineEdit", "float"),
            ("_q_width", "QLineEdit", "float"),
            ("_number_of_samples", "QLineEdit", "int"),
            ("_vectors_per_shell", "QLineEdit", "int"),
            ("_force_equal_weights", "QCheckBox", "bool"),
            ("_axis_1", "VectorWidget", "float"),
            ("_axis_2", "VectorWidget", "float"),
        ]
        return input_list

    def update_item(self) -> None:
        if self._list_item is None:
            return
        self._list_item.setData(self._name, role=Qt.ItemDataRole.DisplayRole)
        self._list_item.setText(self._name)

    def create_resolution_params(self) -> tuple[str, dict[str, float]]:
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
        mdanse_tuple = (WIDGET_TEXT_MAP[self._resolution_type], results)
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

    def create_q_vector_params(
        self, sample_configuration: Trajectory | None = None
    ) -> tuple[str, QVecParamDict]:
        if not self._configured:
            return

        cov_type = self._qvector_type

        try:
            qvec_generator = IQVectors.create(cov_type, trajectory=sample_configuration)
        except ValueError:
            return ("No qvectors", {})
        except AttributeError:
            return (cov_type, {})

        param_dictionary: QVecParamDict = {}
        _q_step, _q_min, _q_max, _q_width = self.sanitize_numbers()

        try:
            conversion_factor = measure(1.0, iunit=self._q_unit).toval("1/nm")
        except Exception as err:
            raise ValueError(f"Could not convert unit: {self._q_unit}") from err

        conversion_factor = float(conversion_factor)

        if "shells" in qvec_generator.parameters:
            q_step = round(conversion_factor * float(_q_step), 6)
            q_min = round(conversion_factor * float(_q_min), 6)
            q_max = round(conversion_factor * float(_q_max), 6)
            param_dictionary["shells"] = (q_min, q_max, q_step)

        if "width" in qvec_generator.parameters:
            width = round(conversion_factor * float(_q_width), 6)
            param_dictionary["width"] = width
        if "n_samples" in qvec_generator.parameters:
            num_samples = int(self._number_of_samples)
            param_dictionary["n_samples"] = num_samples
        if "n_vectors" in qvec_generator.parameters:
            num_vectors = int(self._vectors_per_shell)
            param_dictionary["n_vectors"] = num_vectors

        if "axis" in qvec_generator.parameters:
            ax_vector = [float(x) for x in self._axis_1.split(",")]
            param_dictionary["axis"] = ax_vector

        if "axis_1" in qvec_generator.parameters:
            ax_vector = [float(x) for x in self._axis_1.split(",")]
            param_dictionary["axis_1"] = ax_vector

        if "axis_2" in qvec_generator.parameters:
            ax_vector = [float(x) for x in self._axis_2.split(",")]
            param_dictionary["axis_2"] = ax_vector

        if "force_equal_weights" in qvec_generator.parameters:
            param_dictionary["force_equal_weights"] = bool(self._force_equal_weights)

        return (cov_type, param_dictionary)

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

    def __init__(self, *args, header: str = "", footer: str = "", **kwargs):
        self._header = header
        self._footer = footer
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
    def append_text(self, new_text: str) -> None:
        self.append(new_text)

    def filter(
        self, instrument_object: SimpleInstrument, line_break: str = "<br />"
    ) -> str:
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
        return f"""\
{(self._header + line_break) if self._header else ""}\
<b>{instrument_object._name}</b>{line_break * 2}\
MDANSE resolution input{line_break}\
{instrument_object.create_resolution_params()}{line_break}\
MDANSE q-vector generator input{line_break}\
{instrument_object.create_q_vector_params()}{line_break}\
{(line_break + self._footer) if self._footer else ""}\
"""
