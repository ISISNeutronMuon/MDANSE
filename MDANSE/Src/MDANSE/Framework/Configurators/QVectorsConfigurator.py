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
    isotropically or anistropically, on a lattice or randomly.

    """

    _default = (
        "SphericalLatticeQVectors",
        {"shells": (0.1, 5, 0.1), "width": 0.1, "n_vectors": 50, "seed": 0},
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
        self.error_status = "NONE"
        try:
            if not isinstance(value, tuple):
                raise Exception(f"Q vectors setting must be a tuple {value}")

            try:
                generator_name, parameters = value
            except ValueError:
                raise Exception(f"Invalid q vectors settings {value}")

            generator = IQVectors.create(
                generator_name,
                trajConfig["instance"].configuration(0),
            )
            try:
                generator.setup(parameters)
            except Exception:
                raise Exception(f"Could not configure q vectors using {parameters}")

            try:
                generator_success = generator.generate()
            except Exception:
                raise Exception(
                    "Q Vector parameters were parsed correctly, but caused an error. Invalid values?"
                )

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
            # self["type"] = generator._type
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

    def preview_output_axis(self):
        """Output the values of |Q| from current parameters.

        Returns
        -------
        list[float]
            Values of |Q|.
        str
            Physical unit of Q.

        """
        if not self.is_configured():
            return None, None
        if not self.valid:
            return None, None
        return self["shells"], "1/nm"
