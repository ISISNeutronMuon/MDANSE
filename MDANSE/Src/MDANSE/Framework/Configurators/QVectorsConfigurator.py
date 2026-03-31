#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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

from typing import Any

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.QVectors.IQVectors import IQVectors

from .IConfigurator import PredictionSettings


class QVectorsConfigurator(IConfigurator):
    """Creates and configures a q-vector generator.

    Reciprocal vectors are used in MDANSE for analysis related to
    scattering experiments, such as dynamic coherent structure
    or elastic incoherent structure factor analysis. In MDANSE, properties
    that depend on Q vectors are always scalar regarding Q vectors
    in the sense that the values of these properties will be computed
    for a given norm of Q vectors and not for a given Q vector.
    Hence, the Q vectors generator supported by MDANSE always generates
    Q vectors on Q-shells, each shell containing a set of Q vectors whose
    norm match the Q shell value within a given tolerance.

    Depending on the generator selected, Q vectors can be generated
    isotropically or anisotropically, on a lattice or randomly.

    """

    _default = (
        "SphericalLatticeQVectors",
        {"shells": (0.1, 5, 0.1), "width": 0.1, "n_vectors": 50, "seed": 0},
    )
    label = "Q vector generator"
    tooltip = "Determines how the q vectors will be generated and grouped into shells."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prediction = PredictionSettings(
            key="shells", label="Q vector shell centres", unit="1/nm"
        )

    def configure(self, value: tuple[str, dict[str, Any]]):
        """Create a vector generator with given parameters.

        Parameters
        ----------
        value : tuple[str, dict[str, Any]]
            Class name and dictionary of input parameters

        """
        if not self.update_needed(value):
            return

        self._original_input = value

        trajConfig = self.configurable[self.dependencies["trajectory"]]
        self.error_status = "OK"
        self.warning_status = ""
        try:
            if not isinstance(value, tuple):
                raise Exception(f"Q vectors setting must be a tuple {value}")

            try:
                generator_name, parameters = value
            except ValueError as err:
                raise Exception(f"Invalid q vectors settings {value}") from err

            generator = IQVectors.create(
                generator_name,
                trajConfig["instance"].unit_cell(0),
            )
            try:
                generator.setup(parameters)
            except Exception as err:
                raise Exception(
                    f"Could not configure q vectors using {parameters}"
                ) from err

            try:
                generator_success = generator.generate()
            except Exception as err:
                raise Exception(
                    "Q Vector parameters were parsed correctly, but caused an error. Invalid values?"
                ) from err

            if not generator_success:
                raise Exception(
                    "Q Vector parameters were parsed correctly, but caused an error. Invalid values?"
                )

            if "q_vectors" not in generator.configuration:
                raise Exception(
                    "Wrong inputs for q-vector generation. At the moment there are no valid Q points."
                )
            if not generator.configuration["q_vectors"]:
                raise Exception("no Q vectors could be generated")

            self["parameters"] = parameters
            self["vector_type"] = generator_name
            self["is_lattice"] = generator.is_lattice
            self["q_vectors"] = generator.configuration["q_vectors"]

        except Exception as err:
            self.error_status = str(err)
            return

        self["shells"] = list(self["q_vectors"].keys())
        self["n_shells"] = len(self["q_vectors"])
        self["value"] = self["q_vectors"]
        self["generator"] = generator
        self.error_status = "OK"

        if None in self["value"].values():
            self.warning_status = "Some of the q vector shells are empty. The corresponding results will be NaN values."
        else:
            self.warning_status = ""
            return

        if all(shell is None for shell in self["value"].values()):
            self.error_status = (
                "All the q vector shells are empty. There will be no valid results."
            )
