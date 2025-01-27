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

        selector = Selector(trajConfig["instance"])
        if not selector.check_valid_json_settings(value):
            self.error_status = "Invalid JSON string."
            return

        self["value"] = value

        selector.load_from_json(value)
        indices = selector.get_idxs()

        self["flatten_indices"] = sorted(list(indices))

        trajConfig = self._configurable[self._dependencies["trajectory"]]

        atoms = trajConfig["instance"].chemical_system.atom_list
        selectedAtoms = [atoms[idx] for idx in self["flatten_indices"]]

        self["selection_length"] = len(self["flatten_indices"])
        self["indices"] = [[idx] for idx in self["flatten_indices"]]

        self["elements"] = [[at] for at in selectedAtoms]
        self["names"] = [at for at in selectedAtoms]
        self["unique_names"] = sorted(set(self["names"]))
        self["masses"] = [
            [trajConfig["instance"].get_atom_property(n, "atomic_weight")]
            for n in self["names"]
        ]
        if self["selection_length"] == 0:
            self.error_status = "The atom selection is empty."
            return
        else:
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

    def get_indices(self):
        indicesPerElement = {}
        for i, v in enumerate(self["names"]):
            if v in indicesPerElement:
                indicesPerElement[v].extend(self["indices"][i])
            else:
                indicesPerElement[v] = self["indices"][i][:]

        return indicesPerElement

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
        info.append(f"Number of selected atoms:{self['selection_length']:d}")
        info.append(f"Selected elements:{self['unique_names']}")

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
        selector = Selector(traj_config["instance"])
        return selector
