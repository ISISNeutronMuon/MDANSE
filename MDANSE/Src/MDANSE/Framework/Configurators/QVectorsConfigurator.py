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
        self._original_input = value

        trajConfig = self._configurable[self._dependencies["trajectory"]]
        if isinstance(value, tuple):
            try:
                generator_name, parameters = value
            except ValueError:
                self.error_status = f"Invalid q vectors settings {value}"
                return
            generator = IQVectors.create(
                generator_name, trajConfig["instance"].configuration(0)
            )
            try:
                generator.setup(parameters)
            except Exception:
                self.error_status = f"Could not configure q vectors using {parameters}"
                return

            try:
                generator_success = generator.generate()
            except Exception:
                self.error_status = "Q Vector parameters were parsed correctly, but caused an error. Invalid values?"
                return
            else:
                if not generator_success:
                    self.error_status = "Q Vector parameters were parsed correctly, but caused an error. Invalid values?"
                    return

            if "q_vectors" not in generator.configuration:
                self.error_status = "Wrong inputs for q-vector generation. At the moment there are no valid Q points."
                return
            if not generator.configuration["q_vectors"]:
                self.error_status = "no Q vectors could be generated"
                return

            self["parameters"] = parameters
            # self["type"] = generator._type
            self["is_lattice"] = generator.is_lattice
            self["q_vectors"] = generator.configuration["q_vectors"]
        else:
            self.error_status = f"Q vectors setting must be a tuple {value}"
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
        if not self._valid:
            return None, None
        return self["shells"], "1/nm"

    def get_information(self) -> str:
        """Return human-readable information about the generated vectors.

        Returns
        -------
        str
            Summary of generated vectors.

        """
        try:
            info = [f"{self['n_shells']} Q shells generated\n"]
        except KeyError:
            return "QVectors could not be configured correctly"
        else:
            for qValue, qVectors in self["q_vectors"].items():
                info.append(f"Shell {qValue}: {len(qVectors)} Q vectors generated\n")

            return "".join(info)
