# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE/Framework/Configurators/MoleculeSelectionConfigurator.py
# @brief     Implements module/class/test MoleculeSelectionConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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
