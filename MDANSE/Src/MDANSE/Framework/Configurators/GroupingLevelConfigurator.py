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

from MDANSE.Framework.Configurators.SingleChoiceConfigurator import (
    SingleChoiceConfigurator,
)


class GroupingLevelConfigurator(SingleChoiceConfigurator):
    """Define how the partial results will be grouped in the output.

    The grouping levels currently supported are:
        * 'atom': no changes are made to the atom selection
        * 'each atom': no changes are made to the atom selection
        * 'molecule': this changes the atom names in the atom selection so
          that it includes the molecule name that they are a part of e.g.
          <H2_O1>/H for a water molecule's hydrogen atom. Job in mdanse will
          sum results based on the atom names so that results like
          f(q,t)/<H2_O1>/H will be obtained.
        * 'each molecule': this changes the atom selection so that the atom
          indices for each molecule will be grouped together. Jobs can then
          run calculations can be run for each group of indices together.
    """

    GROUP_TEMPLATE = "{}/<{}>/{}"
    PAIR_GROUP_TEMPLATE = "{}/<{}><{}>/{}"

    _default = "atom"

    def __init__(self, name: str, choices: list[str] | None = None, **kwargs):
        """
        Parameters
        ----------
        name : str
            The name of the configurator.
        choices : Optional[list[str]]
            The grouping choices allowed for the job that will be
            configured.
        """
        usual_choices = ["atom", "molecule"]

        if choices is None:
            choices = usual_choices

        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)

    def configure(self, value: str):
        """
        Parameters
        ----------
        value : str
            The level of granularity at which the atoms should be grouped
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        if value is None:
            value = "atom"

        value = str(value)

        SingleChoiceConfigurator.configure(self, value)

        trajConfig = self.configurable[self.dependencies["trajectory"]]
        if value == "molecule":
            if len(trajConfig["instance"].chemical_system.unique_molecules()) == 0:
                self.error_status = "The trajectory does not contain molecules."
                return

        self["level"] = value
        self.error_status = "OK"
