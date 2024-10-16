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


from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.QVectors.IQVectors import IQVectors


class QVectorsConfigurator(IConfigurator):
    """
    This Configurator allows to set reciprocal vectors.

    Reciprocal vectors are used in MDANSE for the analysis related to scattering experiments such as dynamic coherent structure
    or elastic incoherent structure factor analysis. In MDANSE, properties that depends on Q vectors are always scalar regarding
    Q vectors in the sense that the values of these properties will be computed for a given norm of Q vectors and not for a given Q vectors.
    Hence, the Q vectors generator supported by MDANSE always generates Q vectors on Q-shells, each shell containing a set of Q vectors whose
    norm match the Q shell value within a given tolerance.

    Depending on the generator selected, Q vectors can be generated isotropically or anistropically, on a lattice or randomly.

    Q vectors can be saved to a user definition and, as such, can be further reused in another MDANSE session.

    To define a new Q vectors generator, you must inherit from MDANSE.Framework.QVectors.QVectors.QVector interface.

    :note: this configurator depends on 'trajectory' configurator to be configured.
    """

    _default = (
        "SphericalLatticeQVectors",
        {"shells": (0.1, 5, 0.1), "width": 0.1, "n_vectors": 50, "seed": 0},
    )

    def configure(self, value):
        """
        Configure a Q vectors generator. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the Q vectors generator definition. It can be a 2-tuple, whose 1st element is the name of the Q vector generator \
        and 2nd element the parameters for this configurator or a string that matches a Q vectors user definition.
        :type value: 2-tuple or str
        """
        self._original_input = value

        trajConfig = self._configurable[self._dependencies["trajectory"]]
        if isinstance(value, tuple):
            try:
                generator, parameters = value
            except ValueError:
                self.error_status = f"Invalid q vectors settings {value}"
                return
            generator = IQVectors.create(
                generator, trajConfig["instance"].chemical_system
            )
            try:
                generator.setup(parameters)
            except:
                self.error_status = f"Could not configure q vectors using {parameters}"
                return

            try:
                generator_success = generator.generate()
            except:
                self.error_status = "Q Vector parameters were parsed correctly, but caused an error. Invalid values?"
                return
            else:
                if not generator_success:
                    self.error_status = "Q Vector parameters were parsed correctly, but caused an error. Invalid values?"
                    return

            if not "q_vectors" in generator.configuration:
                self.error_status = "Wrong inputs for q-vector generation. At the moment there are no valid Q points."
                return
            elif not generator.configuration["q_vectors"]:
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
        self.error_status = "OK"

    def preview_output_axis(self):
        if not self.is_configured():
            return None, None
        if not self._valid:
            return None, None
        return self["shells"], "1/nm"

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        try:
            info = ["%d Q shells generated\n" % self["n_shells"]]
        except KeyError:
            return "QVectors could not be configured correctly"
        else:
            for qValue, qVectors in list(self["q_vectors"].items()):
                info.append(
                    "Shell %s: %d Q vectors generated\n" % (qValue, len(qVectors))
                )

            return "".join(info)
