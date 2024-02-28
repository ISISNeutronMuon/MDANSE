# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE/Framework/Configurators/AtomMappingConfigurator.py
# @brief     Implements module/class/test AtomMappingConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
import json

from MDANSE.Framework.AtomMapping import fill_remaining_labels, check_mapping_valid
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class AtomMappingConfigurator(IConfigurator):
    """The atom mapping configurator.

    Attributes
    ----------
    _default : dict
        The default atom map setting JSON string.
    """

    _default = "{}"

    def configure(self, value) -> None:
        """
        Parameters
        ----------
        value : str
            The atom map setting JSON string.
        """
        if value is None:
            value = self._default

        if not isinstance(value, str):
            self.error_status = "Invalid input value."
            return

        try:
            value = json.loads(value)
        except json.decoder.JSONDecodeError:
            self.error_status = "Unable to load JSON string."
            return

        file_configurator = self._configurable[self._dependencies["input_file"]]
        if not file_configurator._valid:
            self.error_status = "Input file not selected."
            return

        labels = file_configurator.get_atom_labels()
        try:
            fill_remaining_labels(labels, value)
        except AttributeError:
            self.error_status = "Unable to map all atoms."
            return

        if not check_mapping_valid(labels, value):
            self.error_status = "Atom mapping is not valid."
            return

        self.error_status = "OK"
        self["value"] = value

    def get_information(self) -> str:
        """Returns some information on the atom mapping configurator.

        Returns
        -------
        str
            The atom map JSON string.
        """
        if "value" not in self:
            return "Not configured yet\n"

        return str(self["value"])
