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

import itertools
from collections.abc import Iterator, Sequence
from typing import Any

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.NewQVectors import QVectorData, QVectorGenerator


class NewQVectorsConfigurator(IConfigurator):
    """This Configurator allows to set reciprocal vectors.

    Reciprocal vectors are used in MDANSE for the analysis related to
    scattering experiments such as dynamic coherent structure or
    elastic incoherent structure factor analysis.

    Depending on the generator selected, Q vectors can be generated
    isotropically or anistropically, on a lattice or randomly.

    Notes
    -----
    This configurator requires a ``trajectory`` configurator to
    be configured.
    """

    gui_defaults = {
        "n_vectors": (
            "IntegerConfigurator",
            {
                "label": "N vectors",
                "tooltip": "Number of vectors to generate.",
                "default": 50,
                "mini": 1,
            },
        ),
        "shells": (
            "RangeConfigurator",
            {
                "label": "Shells",
                "tooltip": "Set number of shells.",
                "valueType": float,
                "default": (0.1, 5.0, 0.1),
                "mini": 1e-9,
            },
        ),
        "width": (
            "FloatConfigurator",
            {
                "label": "Shell Width",
                "tooltip": "Set variance in shell width.",
                "default": 0.1,
                "mini": 1e-9,
            },
        ),
    }

    _default = {
        "shells": (0.1, 5, 0.1),
        "width": 0.1,
        "n_vectors": 50,
        "generator_name": "LatticeSphericalQVectors",
        "q_radius": 1.0,
        "seed": -1,
        "use_shells": True,
    }

    _self_params = {"shells", "width", "n_vectors", "generator_name"}

    def configure(self, parameters: dict[str, Any]):
        """
        Configure a Q vectors generator.

        Parameters
        ----------
        configuration : ~MDANSE.Framework.Configurable.Configurable
            The current configuration.
        parameters : dict[str, Any]
            The parameters for this configurator.
        """
        self._original_input = parameters

        self.clear()

        if not isinstance(parameters, dict):
            self.error_status = f"Q vectors setting must be a tuple {parameters}"
            return

        if "generator_name" not in parameters:
            self.error_status = f"Invalid q vectors settings {parameters}"
            return

        self["generator_name"] = parameters["generator_name"]
        self["gen_parameters"] = {
            key: parameters[key] for key in parameters.keys() - self._self_params
        }
        self["self_parameters"] = {
            key: parameters[key] for key in parameters.keys() & self._self_params
        }
        self["generator"] = QVectorGenerator.create(
            self["generator_name"], lattice=self.unit_cell(0), **self["gen_parameters"]
        )

        self.update(self["self_parameters"])

        self.error_status = "OK"

    def unit_cell(self, frame: int = 0):
        trajConfig = self._configurable[self._dependencies["trajectory"]]
        try:
            return trajConfig["instance"]._data.unit_cell(frame)._unit_cell
        except Exception:
            return None

    @property
    def q_vecs(self) -> Sequence[QVectorData]:
        yield from map(lambda x: x.q, self["generator"].generate_n(self["n_vectors"]))

    @property
    def shells(self) -> Iterator[Iterator[[QVectorData]]]:
        for shell in range(*self["shells"]):
            yield itertools.islice(
                self["generator"].generate_shell(shell, self["width"]),
                self["n_vectors"],
            )

    def preview_output_axis(self):
        if not self.is_configured() or not self.valid:
            return None, None
        return list(self.q_vecs), "1/nm"

    def get_information(self) -> str:
        """
        Returns string information about this configurator.

        Returns
        -------
        str
            The information about this configurator.
        """

        try:
            info = [f"{self['n_shells']} Q shells generated\n"]
        except KeyError:
            return "QVectors could not be configured correctly"
        else:
            for q_value, q_vectors in self["q_vectors"].items():
                info.append(f"Shell {q_value}: {len(q_vectors)} Q vectors generated\n")

            return "".join(info)
