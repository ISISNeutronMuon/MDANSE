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


from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)
from MDANSE.Framework.AtomSelector import Selector


class AtomTransmutationConfigurator(IConfigurator):
    """
    This configurator allows to define a set of atoms to be transmutated to a given chemical
    element.

    For some analysis it can be necessary to change the nature of the chemical element of a given
    part of the system to have results closer to experience. A good example is to change some
    hydrogen atoms to deuterium in order to fit with experiments where deuteration experiments have
    been performed for improving the contrast and having a better access to the dynamic of a specific part
    of the molecular system.

    :note: this configurator depends on 'trajectory' and 'atom_selection' configurators to be configured
    """

    _default = None

    def configure(self, value):
        """
        Configure an input value. 
        
        The value can be:
        
        #. ``None``: no transmutation is performed
        #. (str,str)-dict: for each (str,str) pair, a transmutation will be performed by parsing \
        the 1st element as an atom selection string and transmutating the corresponding atom \
        selection to the target chemical element stored in the 2nd element
        #. str: the transmutation will be performed by reading the corresponding user definition
        
        :param value: the input value
        :type value: None or (str,str)-dict or str 
        """

        self["value"] = value
        self._original_input = value

        # if the input value is None, do not perform any transmutation
        if value is None:
            return

        if not isinstance(value, (list, tuple)):
            self.error_status = "Invalid input value."
            return

        trajConfig = self._configurable[self._dependencies["trajectory"]]

        self._nTransmutatedAtoms = 0

        selector = Selector(trajConfig["instance"].chemical_system)
        for json_string, element in value:
            # Otherwise, it must be a string that will be found as a user-definition keys
            if not isinstance(json_string, str):
                self.error_status = "Wrong format for atom transmutation configurator."
                return

            if UD_STORE.has_definition(
                trajConfig["basename"], "atom_selection", json_string
            ):
                ud = UD_STORE.get_definition(
                    trajConfig["basename"], "atom_selection", json_string
                )
                indexes = ud["indexes"]
            else:
                selector.update_from_json(json_string, reset_first=True)
                indexes = selector.get_idxs()

            self.transmutate(indexes, element)

            self._nTransmutatedAtoms += len(indexes)

    def transmutate(self, selection, element):
        """
        Transmutates a set of atoms to a given element

        :param selection: the indexes of the atoms to be transmutated
        :type selection: list of int
        :param element: the symbol of the element to which the selected atoms should be transmutated
        :type element: str
        """

        if element not in ATOMS_DATABASE:
            self.error_status = (
                f"the element {element} is not registered in the database"
            )
            return

        atomSelConfigurator = self._configurable[self._dependencies["atom_selection"]]

        for idx in selection:
            try:
                idxInSelection = atomSelConfigurator["flatten_indexes"].index(idx)
            except ValueError:
                pass
            else:
                atomSelConfigurator["names"][idxInSelection] = element
                atomSelConfigurator["elements"][idxInSelection] = [element]

        atomSelConfigurator["unique_names"] = sorted(set(atomSelConfigurator["names"]))
        atomSelConfigurator["masses"] = [
            [ATOMS_DATABASE.get_atom_property(n, "atomic_weight")]
            for n in atomSelConfigurator["names"]
        ]
        self.error_status = "OK"

    def get_information(self):
        """
        Returns some informations the atoms selected for being transmutated.

        :return: the information about the atoms selected for being transmutated.
        :rtype: str
        """

        if "value" not in self:
            return "Not configured yet"

        if self["value"] is None:
            return "No atoms selected for transmutation\n"

        return "Number of transmutated atoms:%d\n" % self._nTransmutatedAtoms
