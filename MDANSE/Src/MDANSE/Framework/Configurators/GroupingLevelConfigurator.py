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

import collections

from MDANSE.Chemistry.GroupingTool import GROUPING_LABELS
from MDANSE.Framework.Configurators.SingleChoiceConfigurator import (
    SingleChoiceConfigurator,
)


class GroupingLevelConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to choose the level of granularity in the atom selection.

    When reading the trajectory, the level of granularity will be applied by grouping the atoms of the selection
    to a single dummy-atoms located on the center of gravity of those atoms.

    The level of granularity currently supported are:

    * 'atom': no grouping will be performed
    * 'individual molecules': the atoms that belongs to any molecule will be grouped as a single atom per object
    * 'average over molecules': results will be grouped per molecule type
    """

    _default = "atom"

    def __init__(self, name, choices=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration
        :type name: str
        :param choices: the level of granularities allowed for the input value. If None all levels are allowed.
        :type choices: one of ['atom','group','residue','chain','molecule'] or None
        """
        usual_choices = list(GROUPING_LABELS.keys())

        if choices is None:
            choices = usual_choices
        else:
            choices += [x for x in usual_choices if x not in choices]

        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)

    def configure(self, value):
        """
        :param value: the level of granularity at which the atoms should be grouped
        :type value: str
        """
        self._original_input = value

        if value is None:
            value = "atom"

        value = str(value)

        SingleChoiceConfigurator.configure(self, value)

    def get_information(self):
        """
        Returns some informations about this configurator.

        :return: the information about this configurator
        :rtype: str
        """
        if "value" not in self:
            return "Not configured yet\n"

        return f"Grouping level: {self['value']!r}\n"
