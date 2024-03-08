# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/AtomSelectionConfigurator.py
# @brief     Implements module/class/test AtomSelectionConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
import operator
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)
from MDANSE.Framework.AtomSelector import Selector


class AtomSelectionConfigurator(IConfigurator):
    """
    This configurator allows the selection of a specific set of atoms on which the analysis will be performed.

    Without any selection, all the atoms stored into the trajectory file will be selected.

    After the call to :py:meth:`~MDANSE.Framework.Configurators.AtomSelectionConfigurator.AtomSelectionConfigurator.configure` method
    the following keys will be available for this configurator

    #. value: the input value used to configure this configurator
    #. indexes: the sorted (in increasing order) indexes of the selected atoms
    #. n_selected_atoms: the number of selected atoms
    #. elements: a nested-list of the chemical symbols of the selected atoms. The size of the nested list depends on the grouping_level selected via :py:class:`~MDANSE.Framework.Configurators.GroupingLevelConfigurator.GroupingLevelConfigurator` configurator.

    :note: this configurator depends on :py:class:`~MDANSE.Framework.Configurators.HDFTrajectoryConfigurator.HDFTrajectoryConfigurator` and :py:class:`~MDANSE.Framework.Configurators.GroupingLevelConfigurator.GroupingLevelConfigurator` configurators to be configured
    """

    _default = '{"all": true}'

    def configure(self, value):
        """
        Configure an input value.

        The value must be a string that can be either an atom selection string or a valid user definition.

        :param value: the input value
        :type value: str
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

    def get_natoms(self):
        nAtomsPerElement = {}
        for v in self["names"]:
            if v in nAtomsPerElement:
                nAtomsPerElement[v] += 1
            else:
                nAtomsPerElement[v] = 1

        return nAtomsPerElement

    def get_indexes(self):
        indexesPerElement = {}
        for i, v in enumerate(self["names"]):
            if v in indexesPerElement:
                indexesPerElement[v].extend(self["indexes"][i])
            else:
                indexesPerElement[v] = self["indexes"][i][:]

        return indexesPerElement

    def get_information(self):
        """
        Returns some informations the atom selection.

        :return: the information about the atom selection.
        :rtype: str
        """

        if "selection_length" not in self:
            return "Not configured yet\n"

        info = []
        info.append("Number of selected atoms:%d" % self["selection_length"])
        info.append("Selected elements:%s" % self["unique_names"])

        return "\n".join(info) + "\n"

    def get_selector(self) -> Selector:
        traj_config = self._configurable[self._dependencies["trajectory"]]
        selector = Selector(traj_config["instance"].chemical_system)
        return selector
