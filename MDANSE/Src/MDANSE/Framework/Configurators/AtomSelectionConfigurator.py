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
import operator
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.AtomSelector import Selector


class AtomSelectionConfigurator(IConfigurator):
    """This configurator allows the selection of a specific set of
    atoms on which the analysis will be performed. The defaults setting
    selects all atoms.

    Attributes
    ----------
    _default : str
        The defaults selection setting.
    """

    _default = '{"all": true}'

    def configure(self, value: str) -> None:
        """Configure an input value.

        Parameters
        ----------
        value : str
            The selection setting in a json readable format.
        """
        trajConfig = self._configurable[self._dependencies["trajectory"]]

        if value is None:
            value = self._default

        if not isinstance(value, str):
            self.error_status = "Invalid input value."
            return

        selector = Selector(trajConfig["instance"].chemical_system)
        if not selector.check_valid_json_settings(value):
            self.error_status = "Invalid JSON string."
            return

        self["value"] = value

        selector.update_from_json(value)
        indexes = selector.get_idxs()

        self["flatten_indexes"] = sorted(list(indexes))

        trajConfig = self._configurable[self._dependencies["trajectory"]]

        atoms = sorted(
            trajConfig["instance"].chemical_system.atom_list,
            key=operator.attrgetter("index"),
        )
        selectedAtoms = [atoms[idx] for idx in self["flatten_indexes"]]

        self["selection_length"] = len(self["flatten_indexes"])
        self["indexes"] = [[idx] for idx in self["flatten_indexes"]]

        self["elements"] = [[at.symbol] for at in selectedAtoms]
        self["names"] = [at.symbol for at in selectedAtoms]
        self["unique_names"] = sorted(set(self["names"]))
        self["masses"] = [
            [ATOMS_DATABASE.get_atom_property(n, "atomic_weight")]
            for n in self["names"]
        ]
        self.error_status = "OK"

    def get_natoms(self) -> dict[str, int]:
        """
        Returns
        -------
        dict
            A dictionary of the number of atom per element.
        """
        nAtomsPerElement = {}
        for v in self["names"]:
            if v in nAtomsPerElement:
                nAtomsPerElement[v] += 1
            else:
                nAtomsPerElement[v] = 1

        return nAtomsPerElement

    def get_total_natoms(self) -> int:
        """
        Returns
        -------
        int
            The total number of atoms selected.
        """
        return len(self["names"])

    def get_indexes(self):
        indexesPerElement = {}
        for i, v in enumerate(self["names"]):
            if v in indexesPerElement:
                indexesPerElement[v].extend(self["indexes"][i])
            else:
                indexesPerElement[v] = self["indexes"][i][:]

        return indexesPerElement

    def get_information(self) -> str:
        """
        Returns
        -------
        str
            Some information on the atom selection.
        """
        if "selection_length" not in self:
            return "Not configured yet\n"

        info = []
        info.append("Number of selected atoms:%d" % self["selection_length"])
        info.append("Selected elements:%s" % self["unique_names"])

        return "\n".join(info) + "\n"

    def get_selector(self) -> Selector:
        """
        Returns
        -------
        Selector
            The atom selector object initialised with the trajectories
            chemical system.
        """
        traj_config = self._configurable[self._dependencies["trajectory"]]
        selector = Selector(traj_config["instance"].chemical_system)
        return selector
