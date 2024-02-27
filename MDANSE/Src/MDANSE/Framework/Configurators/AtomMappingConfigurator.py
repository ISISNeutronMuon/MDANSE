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

from MDANSE.Chemistry import ATOMS_DATABASE
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

        if not value:
            self.error_status = "Empty map."
            return

        valid = True
        for k0, v0 in value.items():
            for k1, atm_label in v0.items():
                if atm_label not in ATOMS_DATABASE:
                    valid = False

        if not valid:
            self.error_status = "Unable to map atoms."
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
