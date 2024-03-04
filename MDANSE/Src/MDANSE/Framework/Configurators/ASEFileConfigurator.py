# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/InputFileConfigurator.py
# @brief     Implements module/class/test InputFileConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
from ase.io import iread, read
from ase.io.trajectory import Trajectory as ASETrajectory

from MDANSE.Framework.AtomMapping import AtomLabel
from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class ASEFileConfigurator(FileWithAtomDataConfigurator):
    """
    This Configurator allows to set an input file.
    """

    def parse(self):

        try:
            self._input = ASETrajectory(self["filename"])
        except:
            self._input = iread(
                self["filename"], index="[:]"
            )
            first_frame = read(self["filename"], index=0)
        else:
            first_frame = self._input[0]

        self["element_list"] = first_frame.get_chemical_symbols()

    def get_atom_labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        labels = []
        for atm_label in self["element_list"]:
            label = AtomLabel(atm_label)
            if label not in labels:
                labels.append(label)
        return labels
