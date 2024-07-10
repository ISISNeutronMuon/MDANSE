# **************************************************************************
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
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class MoleculeSelectionConfigurator(IConfigurator):
    """Picks a molecule type present in the trajectory.

    Attributes
    ----------
    _default : str
        Empty by default.
    """

    _default = ""

    def __init__(self, name, choices=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param choices: the list of values allowed for selection.
        :type choices: list
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._choices = []

    @property
    def choices(self):
        return self._choices

    def configure(self, value) -> None:
        """
        Parameters
        ----------
        value : str
            The atom map setting JSON string.
        """
        self._original_input = value
        if value is None:
            value = self._default

        if not isinstance(value, str):
            self.error_status = "Invalid input value."
            return

        trajectory_configurator = self._configurable[self._dependencies["trajectory"]]
        if not trajectory_configurator._valid:
            self.error_status = "Input file not selected."
            return

        self._choices = trajectory_configurator[
            "instance"
        ].chemical_system.unique_molecules()

        if value in self._choices:
            self.error_status = "OK"
            self["value"] = value
        else:
            self.error_status = (
                "The specified molecule name is not present in the trajectory."
            )
            self["value"] = self._default
