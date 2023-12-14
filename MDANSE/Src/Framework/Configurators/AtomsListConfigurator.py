# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/AtomsListConfigurator.py
# @brief     Implements module/class/test AtomsListConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.TrajectoryUtils import find_atoms_in_molecule


class AtomsListConfigurator(IConfigurator):
    """
    This configurator allows of a given list of atom names.

    The atoms has to belong to the same molecule.

    :note: this configurator depends on 'trajectory'
    """

    _default = None

    def __init__(self, name, nAtoms=2, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param nAtoms: the (exact) number of atoms of the list.
        :type nAtoms: int
        """

        IConfigurator.__init__(self, name, **kwargs)

        self._nAtoms = nAtoms

    @property
    def nAtoms(self):
        return self._nAtoms

    def configure(self, value):
        """
        Configure an input value.

        The value must be a string that can be either an atom selection string or a valid user
        definition.

        :param value: the input value
        :type value: str
        """

        traj_configurator = self._configurable[self._dependencies["trajectory"]]

        if UD_STORE.has_definition(
            trajConfig["basename"], "%d_atoms_list" % self._nAtoms, value
        ):
            molecule, atoms = UD_STORE.get_definition(
                trajConfig["basename"], "%d_atoms_list" % self._nAtoms, value
            )
        elif UD_STORE.has_definition(trajConfig["basename"], "atoms_list", value):
            tempdict = UD_STORE.get_definition(
                trajConfig["basename"], "atoms_list", value
            )
            natoms = tempdict["natoms"]
            if not natoms == self._nAtoms:
                raise ValueError(
                    "The atom list must have "
                    + str(self._nAtoms)
                    + " atoms per molecule, but "
                    + str(natoms)
                    + " were found."
                )
            atoms = tempdict["indexes"]
            self["value"] = value
            self["atoms"] = atoms
            self["n_values"] = len(self["atoms"])
            return None  # this new section should be self-sufficient.
        else:
            molecule, atoms = value

        self["value"] = value

        self["atoms"] = find_atoms_in_molecule(
            traj_configurator["instance"].chemical_system, molecule, atoms, True
        )

        self["n_values"] = len(self["atoms"])

    def get_information(self):
        """
        Returns some informations the atom selection.

        :return: the information about the atom selection.
        :rtype: str
        """

        if "atoms" not in self:
            return "No configured yet"

        info = []
        info.append(
            "Number of selected %d-tuplets:%d" % (self._nAtoms, self["n_values"])
        )

        return "\n".join(info)
